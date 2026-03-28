from rest_framework import serializers
from django.utils import timezone
from .models import RFQ, AuctionConfig
from users.serializers import UserSerializer


class AuctionConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuctionConfig
        fields = ['trigger_window_minutes', 'extension_minutes', 'trigger_type']


class RFQCreateSerializer(serializers.ModelSerializer):
    auction_config = AuctionConfigSerializer()

    class Meta:
        model = RFQ
        fields = [
            'id', 'name', 'reference_id',
            'bid_start_time', 'bid_close_time', 'forced_close_time',
            'status', 'auction_config',
        ]
        read_only_fields = ['id', 'status']

    def validate(self, attrs):
        bid_start = attrs.get('bid_start_time')
        bid_close = attrs.get('bid_close_time')
        forced_close = attrs.get('forced_close_time')

        if bid_close and bid_start and bid_close <= bid_start:
            raise serializers.ValidationError(
                "bid_close_time must be after bid_start_time."
            )
        if forced_close and bid_close and forced_close <= bid_close:
            raise serializers.ValidationError(
                "forced_close_time must be after bid_close_time."
            )
        return attrs

    def create(self, validated_data):
        config_data = validated_data.pop('auction_config')
        buyer = self.context['request'].user

        # Set initial_bid_close_time = bid_close_time (immutable copy)
        bid_close_time = validated_data['bid_close_time']
        rfq = RFQ.objects.create(
            buyer=buyer,
            initial_bid_close_time=bid_close_time,
            status=RFQ.Status.DRAFT,
            **validated_data,
        )
        AuctionConfig.objects.create(rfq=rfq, **config_data)
        return rfq


class RFQListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing page — includes denormalized fields."""
    buyer_name = serializers.CharField(source='buyer.name', read_only=True)
    trigger_type = serializers.CharField(source='auction_config.trigger_type', read_only=True)

    class Meta:
        model = RFQ
        fields = [
            'id', 'name', 'reference_id', 'buyer_name',
            'bid_start_time', 'bid_close_time', 'initial_bid_close_time',
            'forced_close_time', 'status', 'current_lowest_bid',
            'trigger_type', 'created_at',
        ]


class RFQDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail page."""
    buyer = UserSerializer(read_only=True)
    auction_config = AuctionConfigSerializer(read_only=True)

    class Meta:
        model = RFQ
        fields = [
            'id', 'name', 'reference_id', 'buyer',
            'bid_start_time', 'bid_close_time', 'initial_bid_close_time',
            'forced_close_time', 'status', 'current_lowest_bid',
            'auction_config', 'created_at', 'updated_at',
        ]
