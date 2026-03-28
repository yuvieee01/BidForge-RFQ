from rest_framework import generics, filters, status
from rest_framework.response import Response
from django.utils import timezone

from .models import RFQ
from .serializers import RFQCreateSerializer, RFQListSerializer, RFQDetailSerializer
from config.permissions import IsBuyer, IsBuyerOrReadOnly
from config.response import success_response, error_response
from auctions.services.auction_service import update_auction_status


class RFQListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/rfq/  — list all non-deleted RFQs (paginated, filterable by status)
    POST /api/rfq/  — create a new RFQ (buyers only)
    """
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'bid_close_time', 'status']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsBuyer()]
        return [IsBuyerOrReadOnly()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RFQCreateSerializer
        return RFQListSerializer

    def get_queryset(self):
        qs = RFQ.objects.filter(is_deleted=False).select_related('buyer', 'auction_config')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # Sync status for all returned RFQs based on server time
        now = timezone.now()
        updated_ids = []
        for rfq in queryset:
            old = rfq.status
            updated = update_auction_status(rfq, save=True)
            if updated.status != old:
                updated_ids.append(rfq.id)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(success_response(serializer.data))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            rfq = serializer.save()
            return Response(
                success_response(RFQDetailSerializer(rfq).data),
                status=status.HTTP_201_CREATED,
            )
        return Response(error_response(str(serializer.errors)), status=status.HTTP_400_BAD_REQUEST)


class RFQDetailView(generics.RetrieveAPIView):
    """
    GET /api/rfq/{id}/ — full RFQ detail with auction config
    """
    permission_classes = [IsBuyerOrReadOnly]
    serializer_class = RFQDetailSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return RFQ.objects.filter(is_deleted=False).select_related('buyer', 'auction_config')

    def retrieve(self, request, *args, **kwargs):
        rfq = self.get_object()
        # Always sync status on read
        rfq = update_auction_status(rfq, save=True)
        serializer = self.get_serializer(rfq)
        return Response(success_response({
            **serializer.data,
            "server_time": timezone.now().isoformat(),
        }))
