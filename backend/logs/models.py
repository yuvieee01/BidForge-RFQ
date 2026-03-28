from django.db import models
from rfq.models import RFQ


class ActivityLog(models.Model):
    class EventType(models.TextChoices):
        BID_SUBMITTED = 'BID_SUBMITTED', 'Bid Submitted'
        AUCTION_EXTENDED = 'AUCTION_EXTENDED', 'Auction Extended'
        AUCTION_STARTED = 'AUCTION_STARTED', 'Auction Started'
        AUCTION_CLOSED = 'AUCTION_CLOSED', 'Auction Closed'
        AUCTION_FORCE_CLOSED = 'AUCTION_FORCE_CLOSED', 'Auction Force Closed'
        RANK_CHANGED = 'RANK_CHANGED', 'Rank Changed'
        L1_CHANGED = 'L1_CHANGED', 'L1 Changed'

    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name='activity_logs')
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    message = models.TextField()
    old_close_time = models.DateTimeField(null=True, blank=True)
    new_close_time = models.DateTimeField(null=True, blank=True)
    # FK to Bid — null for non-bid events (e.g. status changes)
    related_bid = models.ForeignKey(
        'bids.Bid',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='activity_logs',
    )
    # Which trigger rule caused an extension (null if not an extension event)
    trigger_type_used = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'activity_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rfq', 'created_at']),
            models.Index(fields=['event_type']),
        ]

    def __str__(self):
        return f"[{self.event_type}] RFQ {self.rfq_id} @ {self.created_at}"
