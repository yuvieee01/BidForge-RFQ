from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class RFQ(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SCHEDULED = 'scheduled', 'Scheduled'
        ACTIVE = 'active', 'Active'
        EXTENDED = 'extended', 'Extended'
        CLOSED = 'closed', 'Closed'
        FORCE_CLOSED = 'force_closed', 'Force Closed'

    name = models.CharField(max_length=255)
    reference_id = models.CharField(max_length=100, unique=True)
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='rfqs',
        limit_choices_to={'role': 'buyer'},
    )
    bid_start_time = models.DateTimeField()
    # initial_bid_close_time is immutable — set once, never updated
    initial_bid_close_time = models.DateTimeField()
    # bid_close_time is dynamic — updated on each extension
    bid_close_time = models.DateTimeField()
    forced_close_time = models.DateTimeField()
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT)
    # Denormalized for fast listing page reads — always updated inside transactions
    current_lowest_bid = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rfqs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['bid_close_time']),
            models.Index(fields=['forced_close_time']),
            models.Index(fields=['buyer']),
            models.Index(fields=['is_deleted']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(forced_close_time__gt=models.F('bid_close_time')),
                name='rfq_forced_close_after_bid_close',
            ),
            models.CheckConstraint(
                check=models.Q(bid_close_time__gt=models.F('bid_start_time')),
                name='rfq_bid_close_after_start',
            ),
        ]

    def clean(self):
        if self.forced_close_time and self.bid_close_time:
            if self.forced_close_time <= self.bid_close_time:
                raise ValidationError("forced_close_time must be after bid_close_time.")
        if self.bid_close_time and self.bid_start_time:
            if self.bid_close_time <= self.bid_start_time:
                raise ValidationError("bid_close_time must be after bid_start_time.")

    def __str__(self):
        return f"RFQ [{self.reference_id}] — {self.name}"


class AuctionConfig(models.Model):
    class TriggerType(models.TextChoices):
        ANY_BID = 'ANY_BID', 'Any Bid'
        ANY_RANK_CHANGE = 'ANY_RANK_CHANGE', 'Any Rank Change'
        L1_CHANGE = 'L1_CHANGE', 'L1 Change'

    rfq = models.OneToOneField(RFQ, on_delete=models.CASCADE, related_name='auction_config')
    trigger_window_minutes = models.PositiveIntegerField(
        default=5,
        help_text="Extend auction if a trigger event occurs within this many minutes of close."
    )
    extension_minutes = models.PositiveIntegerField(
        default=5,
        help_text="Number of minutes to add when extending."
    )
    trigger_type = models.CharField(
        max_length=20,
        choices=TriggerType.choices,
        default=TriggerType.ANY_BID,
    )

    class Meta:
        db_table = 'auction_configs'

    def __str__(self):
        return f"Config for RFQ {self.rfq_id} — {self.trigger_type}"
