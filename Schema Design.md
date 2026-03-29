## Database Schema

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
