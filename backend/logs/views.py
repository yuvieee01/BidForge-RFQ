from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from rfq.models import RFQ
from .models import ActivityLog
from .serializers import ActivityLogSerializer
from config.response import success_response, error_response
from config.pagination import StandardResultsPagination


class ActivityLogListView(APIView):
    """
    GET /api/logs/{rfq_id}/
    Returns paginated activity log for an RFQ, newest first.
    Filterable by event_type query param.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, rfq_id):
        try:
            RFQ.objects.get(id=rfq_id, is_deleted=False)
        except RFQ.DoesNotExist:
            return Response(error_response("RFQ not found."), status=status.HTTP_404_NOT_FOUND)

        logs = ActivityLog.objects.filter(rfq_id=rfq_id).order_by('-created_at')

        event_type = request.query_params.get('event_type')
        if event_type:
            logs = logs.filter(event_type=event_type)

        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(logs, request)
        if page is not None:
            serializer = ActivityLogSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ActivityLogSerializer(logs, many=True)
        return Response(success_response(serializer.data))
