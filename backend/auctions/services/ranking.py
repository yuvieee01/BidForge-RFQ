"""
ranking.py — Ranking calculation for British Auction.

Rules:
- Lower total_amount = better rank (L1 = lowest).
- Ties broken by earlier created_at (first-come advantage).
- Excludes soft-deleted bids.
"""
from bids.models import Bid


def calculate_rankings(rfq_id: int) -> list[dict]:
    """
    Return ordered list of active bids with rank labels.
    Returns:
        [
            {
                "rank": 1,
                "label": "L1",
                "bid_id": ...,
                "supplier_id": ...,
                "supplier_name": ...,
                "total_amount": ...,
                "freight_charges": ...,
                "origin_charges": ...,
                "destination_charges": ...,
                "transit_time": ...,
                "validity": ...,
                "created_at": ...,
            },
            ...
        ]
    """
    bids = (
        Bid.objects
        .filter(rfq_id=rfq_id, is_deleted=False)
        .select_related('supplier')
        .order_by('total_amount', 'created_at')
    )

    rankings = []
    for idx, bid in enumerate(bids, start=1):
        rankings.append({
            "rank": idx,
            "label": f"L{idx}",
            "bid_id": bid.id,
            "supplier_id": bid.supplier_id,
            "supplier_name": bid.supplier.name,
            "total_amount": str(bid.total_amount),
            "freight_charges": str(bid.freight_charges),
            "origin_charges": str(bid.origin_charges),
            "destination_charges": str(bid.destination_charges),
            "transit_time": bid.transit_time,
            "validity": bid.validity,
            "created_at": bid.created_at.isoformat(),
        })

    return rankings


def detect_rank_change(old_ranking: list[dict], new_ranking: list[dict]) -> bool:
    """
    Return True if any supplier's rank changed between old and new rankings.
    Compares by supplier_id → rank position.
    """
    old_map = {r["supplier_id"]: r["rank"] for r in old_ranking}
    new_map = {r["supplier_id"]: r["rank"] for r in new_ranking}

    # Any supplier whose rank changed, or new supplier entered
    for supplier_id, new_rank in new_map.items():
        if old_map.get(supplier_id) != new_rank:
            return True
    return False


def detect_l1_change(old_ranking: list[dict], new_ranking: list[dict]) -> bool:
    """
    Return True if the L1 (lowest bid) supplier changed.
    """
    old_l1 = old_ranking[0]["supplier_id"] if old_ranking else None
    new_l1 = new_ranking[0]["supplier_id"] if new_ranking else None
    return old_l1 != new_l1
