# High-Level Design — British Auction RFQ System

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)              │
│                                                             │
│  LoginPage  ──►  AuctionListingPage  ──►  AuctionDetailPage │
│                       RFQCreatePage                         │
│                                                             │
│  Services Layer (axios)    Hooks (usePolling, useServerTime) │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP/JSON (JWT Bearer)
                               │ Proxy via Vite dev server
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (Django + DRF)                   │
│                                                             │
│  /api/auth/   /api/rfq/   /api/bids/   /api/auction/        │
│                           /api/logs/                        │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Auction Service Layer                   │   │
│  │  ranking.py │ trigger.py │ extension.py │ status.py  │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │  (rfq_db)       │
                    └─────────────────┘
```

---

## 2. Database Schema

```
users
  id, email (unique), name, role (buyer|supplier), password_hash,
  is_active, is_staff, created_at

rfqs
  id, name, reference_id (unique), buyer_id → users,
  bid_start_time, initial_bid_close_time (immutable),
  bid_close_time (dynamic),  forced_close_time,
  status (draft|scheduled|active|extended|closed|force_closed),
  current_lowest_bid (denormalized),
  is_deleted, created_at, updated_at
  Constraints: forced_close > bid_close, bid_close > bid_start

auction_configs
  id, rfq_id → rfqs (1:1),
  trigger_window_minutes, extension_minutes,
  trigger_type (ANY_BID|ANY_RANK_CHANGE|L1_CHANGE)

bids
  id, rfq_id → rfqs, supplier_id → users,
  total_amount, freight_charges, origin_charges,
  destination_charges, transit_time, validity,
  is_deleted, created_at
  Constraint: total_amount > 0
  Index: (rfq_id, total_amount), (rfq_id, created_at)

activity_logs
  id, rfq_id → rfqs, event_type, message,
  old_close_time, new_close_time,
  related_bid_id → bids (nullable),
  trigger_type_used (nullable),
  created_at
  Index: (rfq_id, created_at)
```

---

## 3. Request Flow — Bid Submission

```
Supplier POST /api/bids/
       │
       ▼
  BidSubmitView
       │
       ├─ Deserialize + validate numeric fields
       │
       └─ transaction.atomic()
              │
              ├─ select_for_update() → Lock RFQ row
              │
              ├─ update_auction_status(rfq) → sync lifecycle
              │
              ├─ Guard checks:
              │    now < bid_start_time       → 400
              │    now > forced_close_time    → 400
              │    status ∉ {active,extended} → 400
              │    buyer == supplier          → 403
              │    duplicate in 30s           → 429
              │    bid ≥ current L1           → 400
              │
              ├─ snapshot old_ranking = calculate_rankings()
              │
              ├─ Bid.objects.create(...)
              │
              ├─ log BID_SUBMITTED → ActivityLog
              │
              ├─ new_ranking = calculate_rankings()
              │
              ├─ detect_l1_change / detect_rank_change → log
              │
              ├─ update rfq.current_lowest_bid
              │
              └─ should_extend_auction()?
                      ├─ is_within_trigger_window()
                      ├─ trigger_type check
                      └─ YES → extend_auction()
                                   ├─ new_close = min(close+Y, forced)
                                   ├─ rfq.bid_close_time = new_close
                                   ├─ rfq.status = extended
                                   └─ log AUCTION_EXTENDED
       │
       ▼
  Response: { bid, ranking, extended, bid_close_time, server_time }
```

---

## 4. Auction Lifecycle

```
         CREATE RFQ
              │
              ▼
           [draft]  ←─── before bid_start_time
              │
              ▼
        [scheduled]  ←─── bid_start_time in future
              │  (time passes)
              ▼
           [active]  ←─── bid_start_time ≤ now < bid_close_time
              │
         bid arrives
         in trigger window?
              │
         ┌───┴───┐
        YES      NO
         │        │
         ▼        └──→ [active] continues
      [extended]
         │
    bid_close_time passes?
         │
    ┌────┴────┐
   YES       NO
    │         │
    ▼         └──→ [extended] continues
  [closed]
    OR
[force_closed]  ←─── forced_close_time reached (always wins)
```

---

## 5. Extension Trigger Modes

| Mode | Trigger Condition | Use Case |
|------|-----------------|----------|
| `ANY_BID` | Any bid lands in window | Maximum competitive pressure |
| `ANY_RANK_CHANGE` | Any supplier's rank changes | Fair — only when competition changes |
| `L1_CHANGE` | Only L1 (lowest) changes | Minimal extensions, only meaningful changes |

---

## 6. Concurrency Design

- All bid submission wrapped in `transaction.atomic()`
- RFQ row locked with `select_for_update()` for duration of transaction
- Prevents: double extensions, rank calculation on stale data, duplicate bids racing

---

## 7. Frontend — Polling Architecture

```
AuctionDetailPage mounts
        │
        ├─ usePolling(fetchAll, 5000ms)
        │       ├─ GET /auction/{id}/status   → sync server_time offset
        │       ├─ GET /auction/{id}/ranking  → update rankings
        │       └─ GET /logs/{id}/            → update activity feed
        │
        ├─ useServerTime()                    → ticking clock from server offset
        │
        └─ CountdownTimer re-renders each second from server-synced time
```

---

## 8. Security Design

| Concern | Implementation |
|---------|----------------|
| Authentication | JWT Bearer tokens (8h access, 7d refresh) |
| Authorization | IsBuyer / IsSupplier DRF permission classes |
| Rate limiting | DRF UserRateThrottle + bid_submit scope (10/min) |
| Race conditions | select_for_update + transaction.atomic on bid submit |
| Input validation | DRF field validators + DB CHECK constraints |
| Duplicate bids | 30s dedup window per supplier per amount |
| Timezone bugs | Server uses timezone.now() exclusively; client syncs offset |
| CORS | django-cors-headers with explicit allowed origins |
| Secrets | python-decouple .env (never hardcoded) |
