# British Auction RFQ System — Implementation Plan

## Overview

A full-stack British Auction RFQ (Request for Quotation) system where buyers post RFQs and suppliers submit bids. The system implements real British Auction mechanics: lower price wins, and the auction auto-extends when activity occurs within a configurable trigger window — always capped at a hard `forced_close_time`.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.x + Django REST Framework |
| Database | PostgreSQL |
| Frontend | React (Vite) + Tailwind CSS |
| Auth | Simple JWT (djangorestframework-simplejwt) |
| Dev Tools | Git structured commits |

---

## Proposed Changes

### Phase 1: Backend Setup

#### [NEW] `backend/` — Django project scaffold
- `backend/config/` — project settings, urls, wsgi
- `backend/users/` — User model with buyer/supplier roles
- `backend/rfq/` — RFQ model, serializer, views, urls
- `backend/auctions/` — AuctionConfig model + auction_service.py
- `backend/bids/` — Bid model, submit logic, ranking
- `backend/logs/` — ActivityLog model, views

#### Database Models

**User**
```
id, name, email, password, role (buyer|supplier), created_at
```

**RFQ**
```
id, name, reference_id, buyer_id,
bid_start_time, initial_bid_close_time (immutable),
bid_close_time (dynamic — updated on extension),
forced_close_time,
status (draft|scheduled|active|extended|closed|force_closed),
current_lowest_bid (denormalized for fast reads),
created_at
```

**AuctionConfig**
```
rfq_id (1:1), trigger_window_minutes, extension_minutes,
trigger_type (ANY_BID|ANY_RANK_CHANGE|L1_CHANGE)
```

**Bid**
```
id, rfq_id, supplier_id, total_amount, freight_charges,
origin_charges, destination_charges, transit_time, validity,
created_at
```

**ActivityLog**
```
id, rfq_id, event_type, message,
old_close_time, new_close_time,
related_bid_id (FK → Bid, nullable),
trigger_type_used (nullable),
created_at
```

**Indexes:** `rfq_id`, `total_amount`, `bid_close_time`, `forced_close_time`

---

### Phase 2: Auction Service

#### [NEW] `backend/auctions/services/auction_service.py`

```python
is_within_trigger_window(rfq, now) -> bool
detect_rank_change(old_ranking, new_ranking) -> bool
detect_l1_change(old_ranking, new_ranking) -> bool
should_extend_auction(rfq, config, trigger_type, old_ranking, new_ranking) -> bool
extend_auction(rfq, config, bid) -> RFQ          # logs trigger_type_used
calculate_rankings(rfq_id) -> list[dict]
update_auction_status(rfq) -> RFQ                # scheduled→active→extended→force_closed
```

Bid submission wrapped in `select_for_update()` transaction to prevent race conditions.

---

### Phase 3: REST APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register user |
| POST | `/api/auth/login/` | Login (JWT) |
| POST | `/api/rfq/` | Create RFQ |
| GET | `/api/rfq/` | List RFQs |
| GET | `/api/rfq/{id}/` | RFQ detail |
| POST | `/api/bids/` | Submit bid |
| GET | `/api/bids/{rfq_id}/` | Get bids for RFQ |
| GET | `/api/auction/{rfq_id}/status/` | Auction status |
| GET | `/api/auction/{rfq_id}/ranking/` | Ranked bids |
| GET | `/api/logs/{rfq_id}/` | Activity log |

---

### Phase 4: Frontend

#### [NEW] `frontend/` — Vite React app with Tailwind CSS

| Page | Route | Description |
|------|-------|-------------|
| Login/Register | `/login` | Auth flow |
| RFQ Create | `/rfq/create` | Buyer creates RFQ |
| Auction Listing | `/auctions` | All active auctions |
| Auction Detail | `/auction/:id` | Full auction view |

**Features:**
- 5-second polling for live updates
- Countdown timer with visual extension highlight
- Bid ranking table (L1, L2, L3...)
- Activity log feed
- Bid submission form (supplier view)

---

## Auction Extension Logic (Critical)

```
On bid submission:
  1. Validate bid_start_time <= now <= forced_close_time
  2. Save bid
  3. Get old ranking (before this bid)
  4. Recalculate ranking
  5. Check trigger:
     - ANY_BID: always triggers if in window
     - ANY_RANK_CHANGE: triggers if any rank changed
     - L1_CHANGE: triggers only if L1 changed
  6. Check is_within_trigger_window(now)
  7. If both true:
     - new_close = min(bid_close_time + Y, forced_close_time)
     - Update rfq.bid_close_time
     - Log extension event
  8. Log bid submission event
```

---

## Verification Plan

### Automated Tests
```bash
cd backend && python manage.py test
```

Tests cover:
- RFQ validation (forced > close time)
- Bid rejected before start / after forced
- Ranking order correctness
- Extension triggered on ANY_BID
- Extension capped at forced_close_time
- L1_CHANGE trigger correctness

### Manual Verification
- Create RFQ as buyer → verify in listing
- Submit bids as supplier → verify ranking
- Submit bid in trigger window → verify extension
- Verify forced_close_time enforced

---

## Git Commit Plan

1. `chore: project setup` — init git, .gitignore, requirements
2. `feat: models and migrations` — all Django models
3. `feat: rfq api` — RFQ CRUD endpoints
4. `feat: bid api` — bid submission + validation
5. `feat: auction logic` — auction_service.py + extension
6. `feat: frontend pages` — React app
7. `feat: integration` — CORS, API wiring
8. `chore: cleanup and docs` — README, HLD, sample data
