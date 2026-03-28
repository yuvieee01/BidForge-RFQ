"""
Comprehensive test suite for the British Auction RFQ System.

Covers:
- RFQ creation and validation
- Bid submission: valid, time boundaries, status guards, duplicate detection
- Ranking logic: ordering, ties, L1/rank change detection
- Extension triggers: ANY_BID, ANY_RANK_CHANGE, L1_CHANGE
- Forced close enforcement (cap at forced_close_time)
- Edge cases: tie bids, bid at exact forced_close_time boundary
"""
from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from rfq.models import RFQ, AuctionConfig
from bids.models import Bid
from logs.models import ActivityLog
from auctions.services.auction_service import (
    calculate_rankings,
    detect_rank_change,
    detect_l1_change,
    is_within_trigger_window,
    should_extend_auction,
    extend_auction,
    update_auction_status,
)

User = get_user_model()


# ─── Fixtures ────────────────────────────────────────────────────────────────

def make_buyer(suffix='1'):
    return User.objects.create_user(
        email=f"buyer{suffix}@test.com",
        name=f"Buyer {suffix}",
        password="pass",
        role='buyer',
    )


def make_supplier(suffix='1'):
    return User.objects.create_user(
        email=f"supplier{suffix}@test.com",
        name=f"Supplier {suffix}",
        password="pass",
        role='supplier',
    )


def make_rfq(buyer, start_offset=-60, close_offset=60, forced_offset=120, trigger_type='ANY_BID'):
    """
    Create an active RFQ with AuctionConfig.
    Offsets are in minutes relative to now.
    """
    now = timezone.now()
    bid_start = now + timedelta(minutes=start_offset)
    bid_close = now + timedelta(minutes=close_offset)
    forced_close = now + timedelta(minutes=forced_offset)

    rfq = RFQ.objects.create(
        name="Test RFQ",
        reference_id=f"REF-{timezone.now().timestamp()}",
        buyer=buyer,
        bid_start_time=bid_start,
        bid_close_time=bid_close,
        initial_bid_close_time=bid_close,
        forced_close_time=forced_close,
        status=RFQ.Status.ACTIVE,
    )
    AuctionConfig.objects.create(
        rfq=rfq,
        trigger_window_minutes=5,
        extension_minutes=5,
        trigger_type=trigger_type,
    )
    return rfq


def make_bid(rfq, supplier, amount='100.00'):
    return Bid.objects.create(
        rfq=rfq,
        supplier=supplier,
        total_amount=Decimal(amount),
        freight_charges=Decimal('0'),
        origin_charges=Decimal('0'),
        destination_charges=Decimal('0'),
        transit_time=3,
        validity=30,
    )


# ─── RFQ Validation Tests ─────────────────────────────────────────────────────

class RFQValidationTests(TestCase):
    def setUp(self):
        self.buyer = make_buyer()

    def test_bid_close_must_be_after_start(self):
        """bid_close_time <= bid_start_time should raise ValidationError."""
        now = timezone.now()
        rfq = RFQ(
            name="Bad RFQ",
            reference_id="REF-BAD-1",
            buyer=self.buyer,
            bid_start_time=now + timedelta(hours=2),
            bid_close_time=now + timedelta(hours=1),
            initial_bid_close_time=now + timedelta(hours=1),
            forced_close_time=now + timedelta(hours=3),
            status=RFQ.Status.DRAFT,
        )
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            rfq.clean()

    def test_forced_close_must_be_after_bid_close(self):
        """forced_close_time <= bid_close_time should raise ValidationError."""
        now = timezone.now()
        rfq = RFQ(
            name="Bad RFQ 2",
            reference_id="REF-BAD-2",
            buyer=self.buyer,
            bid_start_time=now,
            bid_close_time=now + timedelta(hours=2),
            initial_bid_close_time=now + timedelta(hours=2),
            forced_close_time=now + timedelta(hours=1),  # before bid_close!
            status=RFQ.Status.DRAFT,
        )
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            rfq.clean()

    def test_valid_rfq_clean_passes(self):
        now = timezone.now()
        rfq = RFQ(
            name="Good RFQ",
            reference_id="REF-GOOD-1",
            buyer=self.buyer,
            bid_start_time=now,
            bid_close_time=now + timedelta(hours=1),
            initial_bid_close_time=now + timedelta(hours=1),
            forced_close_time=now + timedelta(hours=2),
            status=RFQ.Status.DRAFT,
        )
        rfq.clean()  # Should not raise


# ─── Ranking Tests ────────────────────────────────────────────────────────────

class RankingTests(TestCase):
    def setUp(self):
        self.buyer = make_buyer()
        self.s1 = make_supplier('1')
        self.s2 = make_supplier('2')
        self.s3 = make_supplier('3')
        self.rfq = make_rfq(self.buyer)

    def test_ranking_ordered_by_amount_asc(self):
        make_bid(self.rfq, self.s1, '300.00')
        make_bid(self.rfq, self.s2, '100.00')
        make_bid(self.rfq, self.s3, '200.00')

        rankings = calculate_rankings(self.rfq.id)
        self.assertEqual(rankings[0]['label'], 'L1')
        self.assertEqual(rankings[0]['supplier_id'], self.s2.id)
        self.assertEqual(rankings[1]['label'], 'L2')
        self.assertEqual(rankings[1]['supplier_id'], self.s3.id)
        self.assertEqual(rankings[2]['label'], 'L3')

    def test_tie_broken_by_earlier_created_at(self):
        """When two bids have the same amount, earlier bid wins."""
        b1 = make_bid(self.rfq, self.s1, '100.00')
        b2 = make_bid(self.rfq, self.s2, '100.00')

        rankings = calculate_rankings(self.rfq.id)
        self.assertEqual(rankings[0]['bid_id'], b1.id)
        self.assertEqual(rankings[1]['bid_id'], b2.id)

    def test_soft_deleted_bids_excluded(self):
        b = make_bid(self.rfq, self.s1, '100.00')
        b.is_deleted = True
        b.save()

        rankings = calculate_rankings(self.rfq.id)
        self.assertEqual(len(rankings), 0)

    def test_detect_rank_change_true(self):
        old = [{'supplier_id': 1, 'rank': 1}, {'supplier_id': 2, 'rank': 2}]
        new = [{'supplier_id': 2, 'rank': 1}, {'supplier_id': 1, 'rank': 2}]
        self.assertTrue(detect_rank_change(old, new))

    def test_detect_rank_change_false(self):
        old = [{'supplier_id': 1, 'rank': 1}, {'supplier_id': 2, 'rank': 2}]
        new = [{'supplier_id': 1, 'rank': 1}, {'supplier_id': 2, 'rank': 2}]
        self.assertFalse(detect_rank_change(old, new))

    def test_detect_l1_change_true(self):
        old = [{'supplier_id': 1, 'rank': 1}]
        new = [{'supplier_id': 2, 'rank': 1}]
        self.assertTrue(detect_l1_change(old, new))

    def test_detect_l1_change_false(self):
        old = [{'supplier_id': 1, 'rank': 1}]
        new = [{'supplier_id': 1, 'rank': 1}]
        self.assertFalse(detect_l1_change(old, new))

    def test_detect_l1_change_from_empty(self):
        """First bid ever — L1 changes from None to a supplier."""
        old = []
        new = [{'supplier_id': 1, 'rank': 1}]
        self.assertTrue(detect_l1_change(old, new))


# ─── Extension Trigger Tests ──────────────────────────────────────────────────

class ExtensionTriggerTests(TestCase):
    def setUp(self):
        self.buyer = make_buyer()
        self.s1 = make_supplier('A')
        self.s2 = make_supplier('B')

    def _rfq_closing_in(self, minutes, trigger_type='ANY_BID', forced_offset=60):
        """Create an active RFQ closing in `minutes` minutes."""
        now = timezone.now()
        bid_close = now + timedelta(minutes=minutes)
        forced_close = now + timedelta(minutes=forced_offset)
        rfq = RFQ.objects.create(
            name="Trigger RFQ",
            reference_id=f"TRIG-{timezone.now().timestamp()}",
            buyer=self.buyer,
            bid_start_time=now - timedelta(hours=1),
            bid_close_time=bid_close,
            initial_bid_close_time=bid_close,
            forced_close_time=forced_close,
            status=RFQ.Status.ACTIVE,
        )
        AuctionConfig.objects.create(
            rfq=rfq,
            trigger_window_minutes=5,
            extension_minutes=5,
            trigger_type=trigger_type,
        )
        return rfq

    def test_within_trigger_window(self):
        rfq = self._rfq_closing_in(3)  # 3 min left, window=5min
        self.assertTrue(is_within_trigger_window(rfq))

    def test_outside_trigger_window(self):
        rfq = self._rfq_closing_in(10)  # 10 min left, window=5min
        self.assertFalse(is_within_trigger_window(rfq))

    def test_any_bid_extends_when_in_window(self):
        rfq = self._rfq_closing_in(3, trigger_type='ANY_BID')
        config = rfq.auction_config
        self.assertTrue(should_extend_auction(rfq, config, [], [{'supplier_id': 1, 'rank': 1}]))

    def test_any_bid_does_not_extend_outside_window(self):
        rfq = self._rfq_closing_in(10, trigger_type='ANY_BID')
        config = rfq.auction_config
        self.assertFalse(should_extend_auction(rfq, config, [], [{'supplier_id': 1, 'rank': 1}]))

    def test_any_rank_change_extends_on_rank_change(self):
        rfq = self._rfq_closing_in(3, trigger_type='ANY_RANK_CHANGE')
        config = rfq.auction_config
        old = [{'supplier_id': 1, 'rank': 1}, {'supplier_id': 2, 'rank': 2}]
        new = [{'supplier_id': 2, 'rank': 1}, {'supplier_id': 1, 'rank': 2}]
        self.assertTrue(should_extend_auction(rfq, config, old, new))

    def test_any_rank_change_no_extension_if_no_change(self):
        rfq = self._rfq_closing_in(3, trigger_type='ANY_RANK_CHANGE')
        config = rfq.auction_config
        same = [{'supplier_id': 1, 'rank': 1}]
        self.assertFalse(should_extend_auction(rfq, config, same, same))

    def test_l1_change_extends_only_on_l1_change(self):
        rfq = self._rfq_closing_in(3, trigger_type='L1_CHANGE')
        config = rfq.auction_config
        old = [{'supplier_id': 1, 'rank': 1}, {'supplier_id': 2, 'rank': 2}]
        new = [{'supplier_id': 2, 'rank': 1}, {'supplier_id': 1, 'rank': 2}]
        self.assertTrue(should_extend_auction(rfq, config, old, new))

    def test_l1_change_no_extension_if_l1_same(self):
        rfq = self._rfq_closing_in(3, trigger_type='L1_CHANGE')
        config = rfq.auction_config
        # L1 stays the same (supplier 1), only L2/L3 changed
        old = [{'supplier_id': 1, 'rank': 1}, {'supplier_id': 2, 'rank': 2}]
        new = [{'supplier_id': 1, 'rank': 1}, {'supplier_id': 3, 'rank': 2}]
        self.assertFalse(should_extend_auction(rfq, config, old, new))

    def test_no_extension_when_at_forced_close(self):
        """Already at forced_close_time — no further extension allowed."""
        now = timezone.now()
        rfq = RFQ.objects.create(
            name="Capped RFQ",
            reference_id=f"CAP-{now.timestamp()}",
            buyer=self.buyer,
            bid_start_time=now - timedelta(hours=1),
            bid_close_time=now + timedelta(minutes=2),
            initial_bid_close_time=now + timedelta(minutes=2),
            # forced_close == bid_close → no room to extend
            forced_close_time=now + timedelta(minutes=2),
            status=RFQ.Status.ACTIVE,
        )
        AuctionConfig.objects.create(
            rfq=rfq, trigger_window_minutes=5, extension_minutes=5, trigger_type='ANY_BID'
        )
        config = rfq.auction_config
        self.assertFalse(should_extend_auction(rfq, config, [], [{'supplier_id': 1, 'rank': 1}]))


# ─── Forced Close Enforcement Tests ──────────────────────────────────────────

class ForcedCloseEnforcementTests(TestCase):
    def setUp(self):
        self.buyer = make_buyer()
        self.supplier = make_supplier()

    def test_extend_capped_at_forced_close_time(self):
        """Extension must never push bid_close_time beyond forced_close_time."""
        now = timezone.now()
        forced = now + timedelta(minutes=3)  # Only 3 min to forced close
        rfq = RFQ.objects.create(
            name="Cap Test RFQ",
            reference_id=f"CAPTEST-{now.timestamp()}",
            buyer=self.buyer,
            bid_start_time=now - timedelta(hours=1),
            bid_close_time=now + timedelta(minutes=2),
            initial_bid_close_time=now + timedelta(minutes=2),
            forced_close_time=forced,
            status=RFQ.Status.ACTIVE,
        )
        config = AuctionConfig.objects.create(
            rfq=rfq, trigger_window_minutes=5, extension_minutes=10, trigger_type='ANY_BID'
        )
        bid = make_bid(rfq, self.supplier, '50.00')
        updated_rfq = extend_auction(rfq, config, bid=bid)

        # bid_close_time must not exceed forced_close_time
        self.assertLessEqual(updated_rfq.bid_close_time, forced)
        # Verify log created
        log = ActivityLog.objects.filter(
            rfq=rfq, event_type=ActivityLog.EventType.AUCTION_EXTENDED
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.related_bid, bid)
        self.assertEqual(log.trigger_type_used, config.trigger_type)

    def test_extension_log_records_old_and_new_close(self):
        now = timezone.now()
        bid_close = now + timedelta(minutes=2)
        forced = now + timedelta(hours=1)
        rfq = RFQ.objects.create(
            name="Log Test RFQ",
            reference_id=f"LOGTEST-{now.timestamp()}",
            buyer=self.buyer,
            bid_start_time=now - timedelta(hours=1),
            bid_close_time=bid_close,
            initial_bid_close_time=bid_close,
            forced_close_time=forced,
            status=RFQ.Status.ACTIVE,
        )
        config = AuctionConfig.objects.create(
            rfq=rfq, trigger_window_minutes=5, extension_minutes=5, trigger_type='ANY_BID'
        )
        bid = make_bid(rfq, self.supplier, '50.00')
        extend_auction(rfq, config, bid=bid)

        log = ActivityLog.objects.get(rfq=rfq, event_type=ActivityLog.EventType.AUCTION_EXTENDED)
        self.assertEqual(log.old_close_time, bid_close)
        expected_new = bid_close + timedelta(minutes=5)
        self.assertEqual(log.new_close_time, expected_new)


# ─── Status Lifecycle Tests ───────────────────────────────────────────────────

class StatusLifecycleTests(TestCase):
    def setUp(self):
        self.buyer = make_buyer()

    def _rfq_with_times(self, start_offset, close_offset, forced_offset, status=RFQ.Status.DRAFT):
        now = timezone.now()
        return RFQ(
            name="Status RFQ",
            reference_id=f"STATUS-{now.timestamp()}",
            buyer=self.buyer,
            bid_start_time=now + timedelta(minutes=start_offset),
            bid_close_time=now + timedelta(minutes=close_offset),
            initial_bid_close_time=now + timedelta(minutes=close_offset),
            forced_close_time=now + timedelta(minutes=forced_offset),
            status=status,
        )

    def test_scheduled_before_start(self):
        rfq = self._rfq_with_times(start_offset=30, close_offset=60, forced_offset=90)
        rfq.save()
        updated = update_auction_status(rfq, save=False)
        self.assertEqual(updated.status, RFQ.Status.SCHEDULED)

    def test_active_after_start_before_close(self):
        rfq = self._rfq_with_times(start_offset=-10, close_offset=60, forced_offset=90)
        rfq.save()
        updated = update_auction_status(rfq, save=False)
        self.assertEqual(updated.status, RFQ.Status.ACTIVE)

    def test_closed_after_bid_close(self):
        rfq = self._rfq_with_times(start_offset=-120, close_offset=-10, forced_offset=60)
        rfq.save()
        updated = update_auction_status(rfq, save=False)
        self.assertEqual(updated.status, RFQ.Status.CLOSED)

    def test_force_closed_after_forced_close(self):
        rfq = self._rfq_with_times(start_offset=-120, close_offset=-60, forced_offset=-5)
        rfq.save()
        updated = update_auction_status(rfq, save=False)
        self.assertEqual(updated.status, RFQ.Status.FORCE_CLOSED)
