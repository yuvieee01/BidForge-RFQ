# British Auction RFQ System

A full-stack **British-style reverse auction** platform where buyers post RFQs and suppliers compete by submitting increasingly lower bids. The auction auto-extends when activity occurs within a configurable trigger window, always capped at a hard `forced_close_time`.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5 + Django REST Framework |
| Database | PostgreSQL |
| Frontend | React (Vite) + Tailwind CSS v4 |
| Auth | JWT (djangorestframework-simplejwt) |

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

---

## Setup — Backend

### 1. Create PostgreSQL Database

```sql
CREATE DATABASE rfq_db;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE rfq_db TO postgres;
```

### 2. Python Environment

```bash
cd "RQF System"
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 3. Environment Config

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your DB credentials and secret key
```

### 4. Migrations + Admin

```bash
cd backend
python manage.py migrate
python manage.py createsuperuser   # optional
```

### 5. Seed Sample Data

```bash
cd backend
python sample_data.py
```

Credentials after seeding:
| Role | Email | Password |
|------|-------|----------|
| Buyer | buyer@demo.com | demo1234 |
| Supplier 1 | supplier1@demo.com | demo1234 |
| Supplier 2 | supplier2@demo.com | demo1234 |
| Supplier 3 | supplier3@demo.com | demo1234 |

### 6. Run Backend

```bash
cd backend
python manage.py runserver
# API available at http://localhost:8000/api/
```

---

## Setup — Frontend

```bash
cd frontend
npm install
npm run dev
# UI at http://localhost:5173
```

---

## API Reference

### Auth
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register/` | Public | Create account |
| POST | `/api/auth/login/` | Public | Get JWT tokens + server_time |
| GET | `/api/auth/me/` | Bearer | Current user + server_time |

### RFQ
| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | `/api/rfq/` | Buyer | Create RFQ with auction config |
| GET | `/api/rfq/?status=active` | Any | List RFQs (filterable, paginated) |
| GET | `/api/rfq/{id}/` | Any | RFQ detail + server_time |

### Bids
| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | `/api/bids/` | Supplier | Submit bid (transactional) |
| GET | `/api/bids/{rfq_id}/` | Any | Paginated bid list |

### Auction
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/auction/{rfq_id}/status/` | Any | Full auction state + server_time |
| GET | `/api/auction/{rfq_id}/ranking/` | Any | Ranked bids (L1, L2, L3…) |

### Logs
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/logs/{rfq_id}/` | Any | Paginated activity log |

All responses use standard envelope:
```json
{ "success": true, "data": {}, "error": null }
```

---

## Auction Rules

### Status Lifecycle
```
draft → scheduled → active → extended → closed
                                      ↘ force_closed
```

### Extension Logic
On every bid submission:
1. Validate: `bid_start_time ≤ now ≤ forced_close_time`, status must be `active` or `extended`
2. Save bid inside `transaction.atomic()` + `select_for_update()` on RFQ
3. Recalculate rankings (ordered by `total_amount ASC`, tiebreak by `created_at ASC`)
4. Check trigger in window:
   - `ANY_BID`: always extends if in window
   - `ANY_RANK_CHANGE`: extends if any supplier's rank changed
   - `L1_CHANGE`: extends only if the L1 (lowest) supplier changed
5. Extend: `new_close = min(bid_close + Y, forced_close)`
6. Log all events to ActivityLog

---

## Running Tests

```bash
cd backend
python manage.py test rfq --verbosity=2
```

Test coverage:
- RFQ time validation
- Ranking with tie-breaking
- All 3 trigger modes (ANY_BID, ANY_RANK_CHANGE, L1_CHANGE)
- Forced close cap enforcement
- Extension audit log verification
- Status lifecycle transitions

---

## Git Log

```
chore: initialize repository
chore(setup): django project scaffold, settings, env config, CORS, JWT
feat(models): User, RFQ, AuctionConfig, Bid, ActivityLog — 6-state lifecycle
feat(auction-logic): split service (ranking, trigger, extension, status)
feat(tests): full coverage — RFQ, bids, triggers, forced close, status
chore(frontend): Vite+React, Tailwind, services, hooks, shared components
feat(frontend): Login, RFQCreate, AuctionListing, AuctionDetail pages
chore(docs): README, HLD, sample data, requirements.txt
```
