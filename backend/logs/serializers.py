from rest_framework import serializers
from .models import ActivityLog


class ActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'rfq_id', 'event_type', 'message',
            'old_close_time', 'new_close_time',
            'related_bid_id', 'trigger_type_used',
            'created_at',
        ]
