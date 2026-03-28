"""
trigger.py — Extension trigger evaluation for British Auction.

Supported trigger types:
  ANY_BID         — any bid within the trigger window causes extension.
  ANY_RANK_CHANGE — any rank change (a new supplier appears higher) triggers extension.
  L1_CHANGE       — only L1 (lowest bid) changing triggers extension.
"""
from django.utils import timezone
from rfq.models import RFQ, AuctionConfig
from .ranking import detect_rank_change, detect_l1_change


def is_within_trigger_window(rfq: RFQ, now=None) -> bool:
    """
    Return True if `now` falls within the trigger window before bid_close_time.
    Trigger window = [bid_close_time - trigger_window_minutes, bid_close_time]
    """
    if now is None:
        now = timezone.now()

    try:
        config = rfq.auction_config
    except AuctionConfig.DoesNotExist:
        return False

    from datetime import timedelta
    window_start = rfq.bid_close_time - timedelta(minutes=config.trigger_window_minutes)
    return window_start <= now <= rfq.bid_close_time


def should_extend_auction(
    rfq: RFQ,
    config: AuctionConfig,
    old_ranking: list[dict],
    new_ranking: list[dict],
    now=None,
) -> bool:
    """
    Return True if the extension conditions are fully met:
      1. Bid occurred within trigger window.
      2. Trigger condition is satisfied based on trigger_type.
      3. There is still room to extend (bid_close_time < forced_close_time).
    """
    if now is None:
        now = timezone.now()

    # Condition 1: Must still have room to extend
    if rfq.bid_close_time >= rfq.forced_close_time:
        return False

    # Condition 2: Must be within trigger window
    if not is_within_trigger_window(rfq, now):
        return False

    # Condition 3: Trigger-type-specific check
    trigger = config.trigger_type

    if trigger == AuctionConfig.TriggerType.ANY_BID:
        return True

    if trigger == AuctionConfig.TriggerType.ANY_RANK_CHANGE:
        return detect_rank_change(old_ranking, new_ranking)

    if trigger == AuctionConfig.TriggerType.L1_CHANGE:
        return detect_l1_change(old_ranking, new_ranking)

    return False
