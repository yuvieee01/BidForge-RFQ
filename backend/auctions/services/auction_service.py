"""
auction_service.py — Public facade for all auction business logic.

Import from here in views and tests. Do not import sub-modules directly.
"""
from .ranking import calculate_rankings, detect_rank_change, detect_l1_change
from .trigger import is_within_trigger_window, should_extend_auction
from .extension import extend_auction
from .status import update_auction_status

__all__ = [
    "calculate_rankings",
    "detect_rank_change",
    "detect_l1_change",
    "is_within_trigger_window",
    "should_extend_auction",
    "extend_auction",
    "update_auction_status",
]
