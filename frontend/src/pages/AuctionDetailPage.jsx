import { useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { auctionService, logService, bidService } from '../services';
import { usePolling } from '../hooks/usePolling';
import { setServerTimeOffset } from '../hooks/useServerTime';
import { formatDateTime, formatCurrency } from '../utils/formatters';
import StatusBadge from '../components/StatusBadge';
import CountdownTimer from '../components/CountdownTimer';
import RankingTable from '../components/RankingTable';
import ActivityFeed from '../components/ActivityFeed';
import { useAuth } from '../utils/auth';

const BIDDABLE = new Set(['active', 'extended']);

function InfoCard({ label, value, sub, highlight }) {
  return (
    <div className={`rounded-xl p-4 border ${highlight ? 'bg-blue-500/10 border-blue-500/30' : 'bg-slate-800/40 border-slate-700/40'}`}>
      <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-lg font-bold ${highlight ? 'text-blue-300' : 'text-slate-100'}`}>{value}</p>
      {sub && <p className="text-xs text-slate-600 mt-1">{sub}</p>}
    </div>
  );
}

export default function AuctionDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [auction, setAuction] = useState(null);
  const [rankings, setRankings] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  // Bid form
  const [bidForm, setBidForm] = useState({
    total_amount: '', freight_charges: '0', origin_charges: '0',
    destination_charges: '0', transit_time: '1', validity: '30',
  });
  const [bidError, setBidError] = useState('');
  const [bidSuccess, setBidSuccess] = useState('');
  const [bidLoading, setBidLoading] = useState(false);

  // Extended highlight flash
  const [justExtended, setJustExtended] = useState(false);

  const fetchAll = useCallback(async () => {
    try {
      const [statusRes, rankRes, logRes] = await Promise.all([
        auctionService.status(id),
        auctionService.ranking(id),
        logService.list(id),
      ]);

      const newAuction = statusRes.data.data;
      const newRankings = rankRes.data.data.rankings;
      const newLogs = logRes.data.data?.results ?? logRes.data.data;

      // Sync server time offset
      if (newAuction.server_time) setServerTimeOffset(newAuction.server_time);

      // Detect extension
      if (auction && newAuction.bid_close_time !== auction.bid_close_time) {
        setJustExtended(true);
        setTimeout(() => setJustExtended(false), 5000);
      }

      setAuction(newAuction);
      setRankings(newRankings);
      setLogs(Array.isArray(newLogs) ? newLogs : []);
    } catch (e) {
      // silent
    } finally {
      setLoading(false);
    }
  }, [id, auction]);

  usePolling(fetchAll, 5000, true);

  const updateBid = (k, v) => setBidForm((f) => ({ ...f, [k]: v }));

  const handleBidSubmit = async (e) => {
    e.preventDefault();
    setBidError('');
    setBidSuccess('');
    setBidLoading(true);

    try {
      const payload = {
        rfq: Number(id),
        total_amount: bidForm.total_amount,
        freight_charges: bidForm.freight_charges || '0',
        origin_charges: bidForm.origin_charges || '0',
        destination_charges: bidForm.destination_charges || '0',
        transit_time: Number(bidForm.transit_time),
        validity: Number(bidForm.validity),
      };
      const res = await bidService.submit(payload);
      const d = res.data.data;
      setBidSuccess(
        `Bid submitted! Your rank: L${d.ranking?.findIndex(r => r.bid_id === d.bid?.id) + 1 || '?'}` +
        (d.extended ? ' · ⚡ Auction extended!' : '')
      );
      setBidForm({ total_amount: '', freight_charges: '0', origin_charges: '0', destination_charges: '0', transit_time: '1', validity: '30' });
      // Immediate refresh
      fetchAll();
    } catch (err) {
      setBidError(err.response?.data?.error || 'Bid submission failed.');
    } finally {
      setBidLoading(false);
    }
  };

  const canBid = user?.role === 'supplier' && auction && BIDDABLE.has(auction.status);
  const isExtended = auction?.status === 'extended' || auction?.was_extended;

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8 space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className={`h-${i === 0 ? 28 : 40} rounded-2xl bg-slate-800/40 animate-pulse`} />
        ))}
      </div>
    );
  }

  if (!auction) {
    return (
      <div className="text-center py-24 text-slate-500">
        <p className="text-5xl mb-4">❌</p>
        <p>Auction not found.</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Extension flash */}
      {justExtended && (
        <div className="px-5 py-3 rounded-xl bg-amber-500/15 border border-amber-500/40 text-amber-300 text-sm font-semibold flex items-center gap-2 animate-pulse">
          ⚡ Auction has been extended!
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <button onClick={() => navigate('/auctions')} className="text-slate-500 hover:text-slate-300 text-sm mb-3 flex items-center gap-1 transition-colors">
            ← All Auctions
          </button>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold text-slate-100">{auction.name}</h1>
            <StatusBadge status={auction.status} />
          </div>
          <p className="text-slate-500 text-sm mt-1 font-mono">{auction.reference_id}</p>
        </div>

        {/* Big countdown */}
        {BIDDABLE.has(auction.status) && (
          <div className={`rounded-2xl p-5 border text-center min-w-40 transition-all duration-500 ${
            justExtended || isExtended
              ? 'bg-amber-500/10 border-amber-500/40'
              : 'bg-slate-900/80 border-slate-700/50'
          }`}>
            <CountdownTimer
              targetTime={auction.bid_close_time}
              label="Closes in"
              urgent
              extended={isExtended}
            />
            {isExtended && (
              <p className="text-xs text-slate-500 mt-2">
                Original: {formatDateTime(auction.initial_bid_close_time)}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Info cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <InfoCard
          label="Current L1 Bid"
          value={auction.current_lowest_bid ? formatCurrency(auction.current_lowest_bid) : 'No bids'}
          highlight={!!auction.current_lowest_bid}
        />
        <InfoCard
          label="Bid Close"
          value={formatDateTime(auction.bid_close_time)}
          sub={isExtended ? `Original: ${formatDateTime(auction.initial_bid_close_time)}` : undefined}
        />
        <InfoCard label="Forced Close" value={formatDateTime(auction.forced_close_time)} />
        <InfoCard
          label="Extension Rule"
          value={auction.auction_config?.trigger_type?.replace(/_/g, ' ') || '—'}
          sub={auction.auction_config ? `${auction.auction_config.trigger_window_minutes}min window · +${auction.auction_config.extension_minutes}min` : undefined}
        />
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Rankings — takes 2/3 width */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Live Rankings</h2>
              <span className="text-xs text-slate-500">{rankings.length} bid{rankings.length !== 1 ? 's' : ''}</span>
            </div>
            <RankingTable rankings={rankings} showSupplier={true} />
          </div>

          {/* Bid Form — suppliers only, only when active */}
          {user?.role === 'supplier' && (
            <div className={`bg-slate-900/60 border rounded-2xl p-5 transition-all duration-300 ${
              canBid ? 'border-blue-500/30' : 'border-slate-800/50 opacity-60'
            }`}>
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
                {canBid ? '📥 Submit Your Bid' : '🔒 Bidding Closed'}
              </h2>
              {canBid && (
                <form onSubmit={handleBidSubmit} className="space-y-4">
                  {/* Current L1 hint */}
                  {rankings.length > 0 && (
                    <div className="px-4 py-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300">
                      Current L1: <strong>{formatCurrency(rankings[0].total_amount)}</strong> — your bid must be lower.
                    </div>
                  )}
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {[
                      { k: 'total_amount', label: 'Total Amount ₹', required: true, step: '0.01', min: '0.01' },
                      { k: 'freight_charges', label: 'Freight ₹', step: '0.01', min: '0' },
                      { k: 'origin_charges', label: 'Origin Charges ₹', step: '0.01', min: '0' },
                      { k: 'destination_charges', label: 'Destination ₹', step: '0.01', min: '0' },
                      { k: 'transit_time', label: 'Transit (days)', type: 'number', min: '1' },
                      { k: 'validity', label: 'Validity (days)', type: 'number', min: '1' },
                    ].map(({ k, label, required, step, min, type = 'number' }) => (
                      <div key={k}>
                        <label className="block text-xs text-slate-500 mb-1">{label}</label>
                        <input
                          type={type}
                          step={step}
                          min={min}
                          value={bidForm[k]}
                          onChange={(e) => updateBid(k, e.target.value)}
                          required={required}
                          className="w-full px-3 py-2 rounded-xl bg-slate-800/60 border border-slate-700/50 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50 transition-all text-sm"
                        />
                      </div>
                    ))}
                  </div>

                  {bidError && (
                    <div className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                      {bidError}
                    </div>
                  )}
                  {bidSuccess && (
                    <div className="px-4 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm font-medium">
                      ✓ {bidSuccess}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={bidLoading}
                    className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-500 active:scale-95 text-white font-semibold text-sm transition-all shadow-lg shadow-blue-900/30 disabled:opacity-50"
                  >
                    {bidLoading ? 'Submitting…' : 'Submit Bid →'}
                  </button>
                </form>
              )}
            </div>
          )}
        </div>

        {/* Activity log — 1/3 width */}
        <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-5">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Activity Log</h2>
          <ActivityFeed logs={logs} />
        </div>
      </div>
    </div>
  );
}
