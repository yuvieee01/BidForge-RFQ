"""
sample_data.py — Management command to seed development data.

Usage:
    python manage.py shell < sample_data.py

Creates:
  - 1 buyer
  - 3 suppliers
  - 2 RFQs (1 active/closing soon, 1 scheduled)
  - Bids on the active RFQ
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from rfq.models import RFQ, AuctionConfig
from bids.models import Bid

User = get_user_model()

now = timezone.now()
print("Seeding sample data...")

# ── Users ─────────────────────────────────────────────────────────────────────
buyer = User.objects.get_or_create(email='buyer@demo.com', defaults={
    'name': 'Acme Corp (Buyer)', 'role': 'buyer'
})[0]
buyer.set_password('demo1234')
buyer.save()

suppliers = []
for i, (name, email) in enumerate([
    ('Global Supplies Ltd', 'supplier1@demo.com'),
    ('FastFreight Co',      'supplier2@demo.com'),
    ('BestBid Traders',     'supplier3@demo.com'),
], start=1):
    sup = User.objects.get_or_create(email=email, defaults={'name': name, 'role': 'supplier'})[0]
    sup.set_password('demo1234')
    sup.save()
    suppliers.append(sup)

# ── RFQ 1: Active, closing in 15 minutes ──────────────────────────────────────
rfq1, created = RFQ.objects.get_or_create(reference_id='RFQ-DEMO-001', defaults={
    'name': 'Supply of Industrial Bearings Q2 2025',
    'buyer': buyer,
    'bid_start_time': now - timedelta(hours=2),
    'bid_close_time': now + timedelta(minutes=15),
    'initial_bid_close_time': now + timedelta(minutes=15),
    'forced_close_time': now + timedelta(minutes=60),
    'status': RFQ.Status.ACTIVE,
})
if created:
    AuctionConfig.objects.create(
        rfq=rfq1,
        trigger_window_minutes=5,
        extension_minutes=5,
        trigger_type='ANY_BID',
    )
    # Seed bids
    Bid.objects.create(rfq=rfq1, supplier=suppliers[0], total_amount=Decimal('95000.00'),
        freight_charges=Decimal('2500'), origin_charges=Decimal('1000'),
        destination_charges=Decimal('1500'), transit_time=5, validity=30)
    Bid.objects.create(rfq=rfq1, supplier=suppliers[1], total_amount=Decimal('87500.00'),
        freight_charges=Decimal('3000'), origin_charges=Decimal('800'),
        destination_charges=Decimal('1200'), transit_time=7, validity=45)
    Bid.objects.create(rfq=rfq1, supplier=suppliers[2], total_amount=Decimal('102000.00'),
        freight_charges=Decimal('2000'), origin_charges=Decimal('1200'),
        destination_charges=Decimal('1800'), transit_time=4, validity=30)
    rfq1.current_lowest_bid = Decimal('87500.00')
    rfq1.save(update_fields=['current_lowest_bid'])
    print(f"  Created RFQ 1: {rfq1.reference_id} (active, 3 bids)")

# ── RFQ 2: Scheduled, starts in 30 min ────────────────────────────────────────
rfq2, created = RFQ.objects.get_or_create(reference_id='RFQ-DEMO-002', defaults={
    'name': 'Procurement of Steel Rods — Batch 7',
    'buyer': buyer,
    'bid_start_time': now + timedelta(minutes=30),
    'bid_close_time': now + timedelta(hours=2),
    'initial_bid_close_time': now + timedelta(hours=2),
    'forced_close_time': now + timedelta(hours=3),
    'status': RFQ.Status.SCHEDULED,
})
if created:
    AuctionConfig.objects.create(
        rfq=rfq2,
        trigger_window_minutes=10,
        extension_minutes=10,
        trigger_type='L1_CHANGE',
    )
    print(f"  Created RFQ 2: {rfq2.reference_id} (scheduled)")

print("\nCredentials:")
print("  Buyer:     buyer@demo.com / demo1234")
print("  Supplier1: supplier1@demo.com / demo1234")
print("  Supplier2: supplier2@demo.com / demo1234")
print("  Supplier3: supplier3@demo.com / demo1234")
print("\nDone! ✓")
