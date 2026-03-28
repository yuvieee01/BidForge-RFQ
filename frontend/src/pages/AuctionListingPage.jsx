import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { rfqService } from '../services';
import { usePolling } from '../hooks/usePolling';
import { formatDateTime, formatCurrency } from '../utils/formatters';
import StatusBadge from '../components/StatusBadge';
import CountdownTimer from '../components/CountdownTimer';
import { useAuth } from '../utils/auth';

const STATUS_FILTERS = ['all', 'active', 'extended', 'scheduled', 'closed', 'force_closed', 'draft'];

export default function AuctionListingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [rfqs, setRfqs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [pagination, setPagination] = useState({ count: 0, next: null, previous: null });

  const fetchRfqs = useCallback(async () => {
    try {
      const params = statusFilter !== 'all' ? { status: statusFilter } : {};
      const res = await rfqService.list(params);
      const d = res.data.data;
      setRfqs(d.results ?? d);
      if (d.count !== undefined) setPagination({ count: d.count, next: d.next, previous: d.previous });
    } catch (e) {
      // Silent on poll errors
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  usePolling(fetchRfqs, 5000, true);

  const LIVE_STATUSES = new Set(['active', 'extended']);

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Live Auctions</h1>
          <p className="text-slate-500 text-sm mt-1">
            {pagination.count || rfqs.length} RFQ{(pagination.count || rfqs.length) !== 1 ? 's' : ''} total · Auto-refreshes every 5s
          </p>
        </div>
        {user?.role === 'buyer' && (
          <button
            onClick={() => navigate('/rfq/create')}
            className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 active:scale-95 text-white text-sm font-semibold transition-all shadow-lg shadow-blue-900/30"
          >
            + New RFQ
          </button>
        )}
      </div>

      {/* Status filter tabs */}
      <div className="flex gap-2 flex-wrap mb-6">
        {STATUS_FILTERS.map((s) => (
          <button
            key={s}
            onClick={() => { setStatusFilter(s); setLoading(true); }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all ${
              statusFilter === s
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
            }`}
          >
            {s === 'all' ? 'All' : s.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Cards grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-52 rounded-2xl bg-slate-800/40 animate-pulse" />
          ))}
        </div>
      ) : rfqs.length === 0 ? (
        <div className="text-center py-24 text-slate-500">
          <p className="text-5xl mb-4">📭</p>
          <p className="text-lg font-medium text-slate-400">No auctions found</p>
          <p className="text-sm mt-1">
            {statusFilter !== 'all' ? `No ${statusFilter} auctions.` : 'Create an RFQ to get started.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {rfqs.map((rfq) => {
            const isLive = LIVE_STATUSES.has(rfq.status);
            const isExtended = rfq.status === 'extended';
            return (
              <button
                key={rfq.id}
                onClick={() => navigate(`/auction/${rfq.id}`)}
                className={`text-left p-5 rounded-2xl border transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl group ${
                  isLive
                    ? 'bg-slate-900/80 border-slate-700/60 hover:border-blue-500/50 hover:shadow-blue-900/20'
                    : 'bg-slate-900/40 border-slate-800/60 hover:border-slate-700'
                }`}
              >
                {/* Top row */}
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="min-w-0">
                    <p className="text-xs text-slate-500 font-mono mb-0.5">{rfq.reference_id}</p>
                    <h3 className="font-semibold text-slate-100 text-sm leading-snug line-clamp-2 group-hover:text-blue-300 transition-colors">
                      {rfq.name}
                    </h3>
                  </div>
                  <StatusBadge status={rfq.status} />
                </div>

                {/* Lowest bid */}
                <div className="mb-4">
                  <p className="text-xs text-slate-500 mb-0.5">Current L1 Bid</p>
                  <p className={`text-xl font-bold ${rfq.current_lowest_bid ? 'text-emerald-400' : 'text-slate-600'}`}>
                    {rfq.current_lowest_bid ? formatCurrency(rfq.current_lowest_bid) : 'No bids yet'}
                  </p>
                </div>

                {/* Divider */}
                <div className="border-t border-slate-800 pt-3 space-y-2">
                  {/* Countdown if live */}
                  {isLive ? (
                    <CountdownTimer
                      targetTime={rfq.bid_close_time}
                      label="Closes in"
                      urgent
                      extended={isExtended}
                    />
                  ) : (
                    <div className="text-xs text-slate-500">
                      Closed · {formatDateTime(rfq.bid_close_time)}
                    </div>
                  )}

                  {/* Times row */}
                  <div className="flex justify-between text-xs text-slate-600">
                    <span>Forced close</span>
                    <span className="text-slate-500">{formatDateTime(rfq.forced_close_time)}</span>
                  </div>

                  {/* Extension indicator */}
                  {rfq.trigger_type && (
                    <div className="text-xs text-slate-600 flex justify-between">
                      <span>Trigger</span>
                      <span className="text-slate-500">{rfq.trigger_type?.replace(/_/g, ' ')}</span>
                    </div>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
