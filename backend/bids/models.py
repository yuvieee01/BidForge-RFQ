from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from rfq.models import RFQ


class Bid(models.Model):
    rfq = models.ForeignKey(RFQ, on_delete=models.PROTECT, related_name='bids')
    supplier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='bids',
        limit_choices_to={'role': 'supplier'},
    )
    total_amount = models.DecimalField(
        max_digits=15, decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    freight_charges = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
    )
    origin_charges = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
    )
    destination_charges = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
    )
    transit_time = models.PositiveIntegerField(
        help_text="Transit time in days"
    )
    validity = models.PositiveIntegerField(
        help_text="Bid validity in days"
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bids'
        ordering = ['total_amount', 'created_at']
        indexes = [
            models.Index(fields=['rfq', 'total_amount']),
            models.Index(fields=['rfq', 'created_at']),
            models.Index(fields=['supplier']),
            models.Index(fields=['is_deleted']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(total_amount__gt=0),
                name='bid_total_amount_positive',
            ),
        ]

    def __str__(self):
        return f"Bid by {self.supplier_id} on RFQ {self.rfq_id} — {self.total_amount}"
