from rest_framework import serializers
from .models import Bid
from users.serializers import UserSerializer


class BidSubmitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bid
        fields = [
            'id', 'rfq', 'total_amount', 'freight_charges',
            'origin_charges', 'destination_charges',
            'transit_time', 'validity',
        ]
        read_only_fields = ['id']

    def validate_total_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("total_amount must be greater than 0.")
        return value

    def validate_freight_charges(self, value):
        if value < 0:
            raise serializers.ValidationError("freight_charges cannot be negative.")
        return value

    def validate_origin_charges(self, value):
        if value < 0:
            raise serializers.ValidationError("origin_charges cannot be negative.")
        return value

    def validate_destination_charges(self, value):
        if value < 0:
            raise serializers.ValidationError("destination_charges cannot be negative.")
        return value


class BidListSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    supplier_email = serializers.CharField(source='supplier.email', read_only=True)

    class Meta:
        model = Bid
        fields = [
            'id', 'rfq_id', 'supplier_id', 'supplier_name', 'supplier_email',
            'total_amount', 'freight_charges', 'origin_charges',
            'destination_charges', 'transit_time', 'validity', 'created_at',
        ]
