# 🚀 BidForge: British-Style Reverse Auction System

A high-performance, full-stack **British-style reverse auction** platform. Buyers post Requests for Quotations (RFQs), and suppliers compete in real-time by submitting increasingly lower bids. The system ensures fairness through intelligent auto-extension logic and strict transactional integrity.

---

## 🎯 Why BidForge?

Traditional RFQ systems are static and inefficient. **BidForge** transforms procurement into a dynamic marketplace where:
* **Suppliers** actively compete in real-time for the L1 (lowest) position.
* **Buyers** secure the best possible market price.
* **Concurrency Control** prevents race conditions during high-intensity bidding wars.

---

## 🏗 Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Backend** | Django 5 + Django REST Framework |
| **Database** | PostgreSQL 14+ |
| **Frontend** | React (Vite) + Tailwind CSS v4 |
| **Auth** | JWT (djangorestframework-simplejwt) |

---

## ✨ Key System Features

* ⚡ **Real-Time Ranking** – Dynamic L1, L2, L3 updates with timestamp tie-breaking.
* ⏱ **Auto-Extension (Snipe Protection)** – Auctions extend when activity occurs within the trigger window.
* 🔒 **Forced Close Time** – A hard "dead-stop" cap to prevent infinite bidding loops.
* 🧠 **Configurable Triggers**:
    * `ANY_BID`: Extends on any valid submission.
    * `ANY_RANK_CHANGE`: Extends if a supplier moves up/down the leaderboard.
    * `L1_CHANGE`: Extends only if the top leader is dethroned.
* ⚙️ **Transactional Safety** – Uses `select_for_update` and `atomic()` transactions to handle simultaneous bids.
* 🧾 **Audit Trail** – Comprehensive activity logging for every bid, rank change, and status transition.

---

## 🧠 Auction Mechanics & Logic

### Status Lifecycle
```text
draft → scheduled → active → extended → closed
                                      ↘ force_closed
```

### The Bidding Process
On every bid submission, the backend executes the following:
1. **Validation**: Checks `bid_start_time ≤ now ≤ forced_close_time`.
2. **Locking**: Row-level locking on the RFQ to prevent concurrent update conflicts.
3. **Ranking**: Recalculates the leaderboard based on `total_amount ASC` (Price) and `created_at ASC` (Time).
4. **Trigger Check**: Evaluates if the bid falls within the "Extension Window" based on the selected trigger mode.
5. **Extension**: Calculates `new_close = min(current_close + Y_minutes, forced_close)`.
6. **Time Sync**: All APIs return `server_time` to keep frontend countdowns perfectly aligned.

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+ | Node.js 18+ | PostgreSQL 14+

### 1. Backend Setup
```bash
# Clone and enter directory
cd "RFQ System"
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Environment Config
cp backend/.env.example backend/.env
# Update .env with your PostgreSQL credentials

# Migrations & Data
cd backend
python manage.py migrate
python manage.py createsuperuser  # Optional
python sample_data.py             # Seed demo data
python manage.py runserver        # Starts at http://localhost:8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev  # Starts at http://localhost:5173
```

---

## 📦 Credentials after Seeding
| Role | Email | Password |
| :--- | :--- | :--- |
| **Buyer** | `buyer@demo.com` | `demo1234` |
| **Supplier 1** | `supplier1@demo.com` | `demo1234` |
| **Supplier 2** | `supplier2@demo.com` | `demo1234` |
| **Supplier 3** | `supplier3@demo.com` | `demo1234` |

---

## 📊 API Reference

| Category | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Auth** | POST | `/api/auth/login/` | JWT login + returns `server_time` |
| **RFQ** | POST | `/api/rfq/` | Create RFQ with auction config (Buyer) |
| **RFQ** | GET | `/api/rfq/` | List active/scheduled RFQs |
| **Bids** | POST | `/api/bids/` | Submit bid (Transactional safety) |
| **Auction** | GET | `/api/auction/{id}/status/` | Live auction state & countdowns |
| **Auction** | GET | `/api/auction/{id}/ranking/` | Current Leaderboard (L1, L2, L3...) |

---

## 🧪 Testing & Quality
Run the comprehensive test suite to verify business logic:
```bash
cd backend
python manage.py test rfq --verbosity=2
```
**Coverage Includes:** Ranking tie-breaking, all 3 trigger modes, forced-close enforcement, and race-condition simulation.

---

## 🔮 Future Roadmap
* **WebSockets**: Implement Django Channels for push-based UI updates.
* **Analytics**: Buyer dashboard for price trend visualization.
* **Notifications**: Email alerts for outbid suppliers.
* **Docker**: Containerized deployment via Docker Compose.

---

## 🧾 Git Highlights

* Structured commits following feature-based development.
* Modular auction logic (ranking, trigger, extension, status).
* Clean separation of backend and frontend concerns.

---

## 🎯 Project Takeaway

BidForge demonstrates real-world system design skills by:
* Handling **high-concurrency** transactional systems.
* Designing **time-sensitive** business logic.
* Building **scalable** full-stack applications.
* Maintaining **data integrity** under competitive conditions.
