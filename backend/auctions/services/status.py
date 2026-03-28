"""
status.py — Auction lifecycle status management.

Manages automatic status transitions:
  draft       → scheduled   (before bid_start_time)
  scheduled   → active      (once bid_start_time passes)
  active      → extended    (on extension)
  active/extended → closed  (once bid_close_time passes, not forced)
  any         → force_closed (once forced_close_time passes)

Call update_auction_status() on every read of an RFQ to ensure
status stays consistent with wall clock.
"""
from django.utils import timezone
from rfq.models import RFQ
from logs.models import ActivityLog


def update_auction_status(rfq: RFQ, save: bool = True) -> RFQ:
    """
    Compute the correct status for `rfq` based on timezone.now().
    Persists the change if `save=True` and the status actually changed.

    Returns the (possibly mutated) rfq instance.
    """
    now = timezone.now()
    old_status = rfq.status
    new_status = _compute_status(rfq, now)

    if new_status != old_status:
        rfq.status = new_status
        if save:
            rfq.save(update_fields=['status', 'updated_at'])
            _log_status_transition(rfq, old_status, new_status)

    return rfq


def _compute_status(rfq: RFQ, now) -> str:
    """Pure function — compute expected status without side effects."""
    # Forced close overrides everything
    if now >= rfq.forced_close_time:
        return RFQ.Status.FORCE_CLOSED

    # Auction window has ended normally
    if now >= rfq.bid_close_time:
        # If it was extended and still before forced, it's closed normally
        return RFQ.Status.CLOSED

    # Auction is open
    if now >= rfq.bid_start_time:
        # Keep 'extended' status if already set — it's informative
        if rfq.status == RFQ.Status.EXTENDED:
            return RFQ.Status.EXTENDED
        return RFQ.Status.ACTIVE

    # Not yet started
    if rfq.status == RFQ.Status.DRAFT:
        return RFQ.Status.DRAFT

    return RFQ.Status.SCHEDULED


def _log_status_transition(rfq: RFQ, old_status: str, new_status: str):
    event_map = {
        RFQ.Status.ACTIVE: ActivityLog.EventType.AUCTION_STARTED,
        RFQ.Status.CLOSED: ActivityLog.EventType.AUCTION_CLOSED,
        RFQ.Status.FORCE_CLOSED: ActivityLog.EventType.AUCTION_FORCE_CLOSED,
    }
    event_type = event_map.get(new_status)
    if event_type:
        ActivityLog.objects.create(
            rfq=rfq,
            event_type=event_type,
            message=f"Auction status changed: {old_status} → {new_status}",
        )
