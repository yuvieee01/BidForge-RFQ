from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone

from rfq.models import RFQ
from rfq.serializers import RFQDetailSerializer
from config.response import success_response, error_response
from auctions.services.auction_service import calculate_rankings, update_auction_status


class AuctionStatusView(APIView):
    """
    GET /api/auction/{rfq_id}/status/
    Returns full auction state + server time for frontend timer sync.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, rfq_id):
        try:
            rfq = RFQ.objects.select_related('auction_config', 'buyer').get(
                id=rfq_id, is_deleted=False
            )
        except RFQ.DoesNotExist:
            return Response(error_response("RFQ not found."), status=status.HTTP_404_NOT_FOUND)

        # Always sync status on read
        rfq = update_auction_status(rfq, save=True)
        now = timezone.now()

        try:
            config = rfq.auction_config
            config_data = {
                "trigger_type": config.trigger_type,
                "trigger_window_minutes": config.trigger_window_minutes,
                "extension_minutes": config.extension_minutes,
            }
        except Exception:
            config_data = None

        return Response(success_response({
            "rfq_id": rfq.id,
            "name": rfq.name,
            "reference_id": rfq.reference_id,
            "status": rfq.status,
            "bid_start_time": rfq.bid_start_time.isoformat(),
            "bid_close_time": rfq.bid_close_time.isoformat(),
            "initial_bid_close_time": rfq.initial_bid_close_time.isoformat(),
            "forced_close_time": rfq.forced_close_time.isoformat(),
            "current_lowest_bid": str(rfq.current_lowest_bid) if rfq.current_lowest_bid else None,
            "auction_config": config_data,
            "server_time": now.isoformat(),
            # Was the auction extended from its original close time?
            "was_extended": rfq.bid_close_time != rfq.initial_bid_close_time,
        }))


class AuctionRankingView(APIView):
    """
    GET /api/auction/{rfq_id}/ranking/
    Returns ranked bid list (L1, L2, L3...) with server time.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, rfq_id):
        try:
            rfq = RFQ.objects.get(id=rfq_id, is_deleted=False)
        except RFQ.DoesNotExist:
            return Response(error_response("RFQ not found."), status=status.HTTP_404_NOT_FOUND)

        rfq = update_auction_status(rfq, save=True)
        rankings = calculate_rankings(rfq_id)

        return Response(success_response({
            "rfq_id": rfq_id,
            "status": rfq.status,
            "total_bids": len(rankings),
            "rankings": rankings,
            "server_time": timezone.now().isoformat(),
        }))
