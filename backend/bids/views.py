from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from django.db import transaction
from django.utils import timezone

from rfq.models import RFQ
from logs.models import ActivityLog
from .models import Bid
from .serializers import BidSubmitSerializer, BidListSerializer
from config.permissions import IsSupplier, IsBuyerOrReadOnly
from config.response import success_response, error_response
from config.pagination import StandardResultsPagination
from auctions.services.auction_service import (
    calculate_rankings,
    should_extend_auction,
    extend_auction,
    update_auction_status,
)


class BidRateThrottle(UserRateThrottle):
    scope = 'bid_submit'


# Statuses that allow bids
BIDDABLE_STATUSES = {RFQ.Status.ACTIVE, RFQ.Status.EXTENDED}
# Statuses that never allow bids
CLOSED_STATUSES = {RFQ.Status.CLOSED, RFQ.Status.FORCE_CLOSED}


class BidSubmitView(APIView):
    """
    POST /api/bids/
    Submit a bid on an active auction.

    Fully wrapped in select_for_update() transaction to prevent:
      - Race conditions on concurrent bids
      - Double extensions
      - Incorrect ranking
    """
    permission_classes = [IsSupplier]
    throttle_classes = [BidRateThrottle]

    def post(self, request):
        serializer = BidSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(error_response(str(serializer.errors)), status=status.HTTP_400_BAD_REQUEST)

        rfq_id = serializer.validated_data['rfq'].id
        supplier = request.user

        try:
            with transaction.atomic():
                # Lock the RFQ row for the duration of this transaction
                rfq = RFQ.objects.select_for_update().get(id=rfq_id, is_deleted=False)

                # Sync status with current time before validation
                rfq = update_auction_status(rfq, save=True)

                now = timezone.now()

                # ── Validation Guards ──────────────────────────────────────
                if now < rfq.bid_start_time:
                    return Response(
                        error_response(
                            f"Auction has not started yet. Starts at {rfq.bid_start_time.isoformat()}."
                        ),
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if now > rfq.forced_close_time:
                    return Response(
                        error_response("Auction has passed its forced close time. No further bids accepted."),
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if rfq.status in CLOSED_STATUSES:
                    return Response(
                        error_response(f"Auction is {rfq.status}. Bidding is closed."),
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if rfq.status not in BIDDABLE_STATUSES:
                    return Response(
                        error_response(f"Auction is not accepting bids (status: {rfq.status})."),
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Prevent supplier from bidding on their own RFQ (edge case)
                if rfq.buyer_id == supplier.id:
                    return Response(
                        error_response("Buyers cannot submit bids on their own RFQ."),
                        status=status.HTTP_403_FORBIDDEN,
                    )

                # Duplicate bid guard: reject identical amount from same supplier in last 30s
                recent_duplicate = Bid.objects.filter(
                    rfq=rfq,
                    supplier=supplier,
                    total_amount=serializer.validated_data['total_amount'],
                    is_deleted=False,
                    created_at__gte=now - timezone.timedelta(seconds=30),
                ).exists()
                if recent_duplicate:
                    return Response(
                        error_response(
                            "Duplicate bid: identical amount submitted within the last 30 seconds."
                        ),
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )

                # Snapshot ranking BEFORE this bid (for trigger comparison)
                old_ranking = calculate_rankings(rfq_id)

                # Current L1 amount (bid must beat L1 to be meaningful, but we allow any valid bid)
                # Per spec: enforce bid must be lower than current L1 if there are existing bids
                new_amount = serializer.validated_data['total_amount']
                if old_ranking:
                    current_l1_amount = old_ranking[0]['total_amount']
                    if float(new_amount) >= float(current_l1_amount):
                        return Response(
                            error_response(
                                f"Bid must be lower than current L1 price ({current_l1_amount}). "
                                f"Your bid: {new_amount}."
                            ),
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                # ── Save Bid ───────────────────────────────────────────────
                bid = Bid.objects.create(
                    rfq=rfq,
                    supplier=supplier,
                    **{k: v for k, v in serializer.validated_data.items() if k != 'rfq'},
                )

                # Log bid submission
                ActivityLog.objects.create(
                    rfq=rfq,
                    event_type=ActivityLog.EventType.BID_SUBMITTED,
                    message=(
                        f"Supplier '{supplier.name}' submitted bid of {bid.total_amount} "
                        f"on RFQ '{rfq.name}'."
                    ),
                    related_bid=bid,
                )

                # ── Recalculate Rankings ───────────────────────────────────
                new_ranking = calculate_rankings(rfq_id)

                # Log rank/L1 change events
                from auctions.services.ranking import detect_rank_change, detect_l1_change
                if detect_l1_change(old_ranking, new_ranking):
                    ActivityLog.objects.create(
                        rfq=rfq,
                        event_type=ActivityLog.EventType.L1_CHANGED,
                        message=f"New L1 bid: {bid.total_amount} by '{supplier.name}'.",
                        related_bid=bid,
                    )
                elif detect_rank_change(old_ranking, new_ranking):
                    ActivityLog.objects.create(
                        rfq=rfq,
                        event_type=ActivityLog.EventType.RANK_CHANGED,
                        message=f"Rank change after bid of {bid.total_amount} by '{supplier.name}'.",
                        related_bid=bid,
                    )

                # ── Update Denormalized lowest bid ─────────────────────────
                if new_ranking:
                    rfq.current_lowest_bid = new_ranking[0]['total_amount']
                    rfq.save(update_fields=['current_lowest_bid', 'updated_at'])

                # ── Extension Check ────────────────────────────────────────
                extended = False
                try:
                    config = rfq.auction_config
                    if should_extend_auction(rfq, config, old_ranking, new_ranking, now):
                        rfq = extend_auction(rfq, config, bid=bid)
                        extended = True
                except RFQ.auction_config.RelatedObjectDoesNotExist:
                    pass  # No config → no extension logic

        except RFQ.DoesNotExist:
            return Response(error_response("RFQ not found."), status=status.HTTP_404_NOT_FOUND)

        return Response(success_response({
            "bid": BidListSerializer(bid).data,
            "ranking": new_ranking,
            "extended": extended,
            "bid_close_time": rfq.bid_close_time.isoformat(),
            "forced_close_time": rfq.forced_close_time.isoformat(),
            "server_time": timezone.now().isoformat(),
        }), status=status.HTTP_201_CREATED)


class BidListView(APIView):
    """
    GET /api/bids/{rfq_id}/
    Get all bids for an RFQ, ordered by total_amount ASC (paginated).
    Accessible by authenticated users (buyer sees all; supplier sees all in active auction).
    """
    permission_classes = [IsBuyerOrReadOnly]

    def get(self, request, rfq_id):
        try:
            rfq = RFQ.objects.get(id=rfq_id, is_deleted=False)
        except RFQ.DoesNotExist:
            return Response(error_response("RFQ not found."), status=status.HTTP_404_NOT_FOUND)

        bids = (
            Bid.objects
            .filter(rfq=rfq, is_deleted=False)
            .select_related('supplier')
            .order_by('total_amount', 'created_at')
        )

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(bids, request)
        if page is not None:
            serializer = BidListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = BidListSerializer(bids, many=True)
        return Response(success_response(serializer.data))
