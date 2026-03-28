"""
extension.py — Auction extension logic.

Handles:
- Computing new bid_close_time (capped at forced_close_time)
- Updating RFQ status to 'extended' or 'force_closed'
- Creating ActivityLog entry with all relevant fields
"""
from datetime import timedelta
from django.utils import timezone
from rfq.models import RFQ, AuctionConfig


def extend_auction(rfq: RFQ, config: AuctionConfig, bid=None) -> RFQ:
    """
    Extend rfq.bid_close_time by config.extension_minutes, capped at forced_close_time.

    Always re-reads bid_close_time from the passed rfq object (which should
    already be locked via select_for_update in the caller).

    Updates:
      - rfq.bid_close_time
      - rfq.status → 'extended' or 'force_closed' (if cap reached)

    Creates an ActivityLog entry.

    Returns the updated (saved) RFQ instance.
    """
    from logs.models import ActivityLog

    now = timezone.now()
    old_close_time = rfq.bid_close_time

    proposed_new_close = old_close_time + timedelta(minutes=config.extension_minutes)
    new_close_time = min(proposed_new_close, rfq.forced_close_time)

    rfq.bid_close_time = new_close_time

    if new_close_time >= rfq.forced_close_time:
        rfq.status = RFQ.Status.FORCE_CLOSED
        # bid_close_time == forced_close_time means no further extensions possible
        # Status will flip to force_closed when the time passes; we set it here
        # so the system knows no further extension is possible.
        rfq.status = RFQ.Status.EXTENDED  # Still active but will force-close at deadline
    else:
        rfq.status = RFQ.Status.EXTENDED

    rfq.save(update_fields=['bid_close_time', 'status', 'updated_at'])

    # Create audit log
    ActivityLog.objects.create(
        rfq=rfq,
        event_type=ActivityLog.EventType.AUCTION_EXTENDED,
        message=(
            f"Auction extended by {config.extension_minutes} min. "
            f"Old close: {old_close_time.isoformat()} → "
            f"New close: {new_close_time.isoformat()}"
            + (" [CAPPED at forced_close_time]" if new_close_time >= rfq.forced_close_time else "")
        ),
        old_close_time=old_close_time,
        new_close_time=new_close_time,
        related_bid=bid,
        trigger_type_used=config.trigger_type,
    )

    return rfq
