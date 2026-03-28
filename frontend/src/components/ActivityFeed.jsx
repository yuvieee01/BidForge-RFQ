import { formatDateTime } from '../utils/formatters';

const EVENT_STYLES = {
  AUCTION_EXTENDED:    { icon: '⚡', color: 'text-amber-400', bg: 'bg-amber-400/10 border-amber-500/30' },
  BID_SUBMITTED:       { icon: '📥', color: 'text-blue-400',  bg: 'bg-blue-400/10 border-blue-500/30' },
  L1_CHANGED:          { icon: '🏆', color: 'text-amber-300', bg: 'bg-amber-300/10 border-amber-400/30' },
  RANK_CHANGED:        { icon: '🔀', color: 'text-purple-400',bg: 'bg-purple-400/10 border-purple-500/30' },
  AUCTION_STARTED:     { icon: '🚀', color: 'text-emerald-400',bg: 'bg-emerald-400/10 border-emerald-500/30' },
  AUCTION_CLOSED:      { icon: '🔒', color: 'text-slate-400', bg: 'bg-slate-400/10 border-slate-500/30' },
  AUCTION_FORCE_CLOSED:{ icon: '🛑', color: 'text-red-400',   bg: 'bg-red-400/10 border-red-500/30' },
};

export default function ActivityFeed({ logs = [] }) {
  if (!logs.length) {
    return (
      <div className="text-center py-8 text-slate-500 text-sm">
        No activity yet.
      </div>
    );
  }

  return (
    <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
      {logs.map((log) => {
        const style = EVENT_STYLES[log.event_type] || { icon: '📋', color: 'text-slate-400', bg: 'bg-slate-800 border-slate-700' };
        return (
          <div
            key={log.id}
            className={`flex gap-3 p-3 rounded-lg border text-sm ${style.bg}`}
          >
            <span className="text-lg flex-shrink-0">{style.icon}</span>
            <div className="flex-1 min-w-0">
              <p className={`font-medium ${style.color}`}>
                {log.event_type.replace(/_/g, ' ')}
                {log.trigger_type_used && (
                  <span className="ml-2 text-xs text-slate-500 font-normal">
                    via {log.trigger_type_used}
                  </span>
                )}
              </p>
              <p className="text-slate-300 text-xs mt-0.5 leading-relaxed">{log.message}</p>
              {log.old_close_time && log.new_close_time && (
                <p className="text-xs text-slate-500 mt-1">
                  {formatDateTime(log.old_close_time)} → {formatDateTime(log.new_close_time)}
                </p>
              )}
            </div>
            <time className="text-xs text-slate-500 flex-shrink-0 mt-0.5">
              {formatDateTime(log.created_at)}
            </time>
          </div>
        );
      })}
    </div>
  );
}
