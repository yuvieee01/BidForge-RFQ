import { rankStyle } from '../utils/formatters';

/**
 * RankingTable
 * Props:
 *   rankings — array from GET /auction/{id}/ranking
 *   showSupplier — bool (buyers see names; suppliers only see ranks in competitive mode)
 */
export default function RankingTable({ rankings = [], showSupplier = true }) {
  if (!rankings.length) {
    return (
      <div className="text-center py-12 text-slate-500">
        <p className="text-4xl mb-3">📭</p>
        <p className="text-sm">No bids yet. Be the first to bid.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-700/50">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-700/50 bg-slate-800/60">
            <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-slate-400">Rank</th>
            {showSupplier && (
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-slate-400">Supplier</th>
            )}
            <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-slate-400">Total Amount</th>
            <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-slate-400">Freight</th>
            <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-slate-400">Origin</th>
            <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-slate-400">Destination</th>
            <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-slate-400">Transit (days)</th>
            <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-slate-400">Validity (days)</th>
            <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-slate-400">Submitted</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700/30">
          {rankings.map((row, i) => (
            <tr
              key={row.bid_id}
              className={`transition-colors duration-200 ${i === 0
                  ? 'bg-amber-500/5 hover:bg-amber-500/10'
                  : 'hover:bg-slate-700/20'
                }`}
            >
              <td className="px-4 py-3">
                <span className={`px-2 py-0.5 rounded text-xs font-bold ${rankStyle(row.label)}`}>
                  {row.label}
                </span>
              </td>
              {showSupplier && (
                <td className="px-4 py-3 font-medium text-slate-200">{row.supplier_name}</td>
              )}
              <td className="px-4 py-3 text-right font-semibold text-slate-100">
                ₹{Number(row.total_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </td>
              <td className="px-4 py-3 text-right text-slate-400">
                ₹{Number(row.freight_charges).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </td>
              <td className="px-4 py-3 text-right text-slate-400">
                ₹{Number(row.origin_charges).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </td>
              <td className="px-4 py-3 text-right text-slate-400">
                ₹{Number(row.destination_charges).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </td>
              <td className="px-4 py-3 text-right text-slate-400">{row.transit_time}</td>
              <td className="px-4 py-3 text-right text-slate-400">{row.validity}</td>
              <td className="px-4 py-3 text-right text-slate-500 text-xs">
                {new Date(row.created_at).toLocaleTimeString('en-GB')}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
