/**
 * formatters.js — shared display helpers
 */

/** Format ISO string to readable local date+time */
export function formatDateTime(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false,
  });
}

/** Format a decimal string as currency */
export function formatCurrency(amount, currency = '₹') {
  if (amount == null) return '—';
  return `${currency}${Number(amount).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

/**
 * Return seconds remaining between two dates.
 * Returns 0 if already past.
 */
export function secondsUntil(targetDate, fromDate = new Date()) {
  const diff = Math.floor((new Date(targetDate) - fromDate) / 1000);
  return Math.max(0, diff);
}

/** Format seconds → HH:MM:SS */
export function formatCountdown(totalSeconds) {
  if (totalSeconds <= 0) return '00:00:00';
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  return [h, m, s].map((v) => String(v).padStart(2, '0')).join(':');
}

/** Return Tailwind color classes based on auction status */
export function statusStyle(status) {
  switch (status) {
    case 'active':
      return { bg: 'bg-emerald-500/15', text: 'text-emerald-400', dot: 'bg-emerald-400', label: 'Active' };
    case 'extended':
      return { bg: 'bg-amber-500/15', text: 'text-amber-400', dot: 'bg-amber-400', label: 'Extended' };
    case 'scheduled':
      return { bg: 'bg-blue-500/15', text: 'text-blue-400', dot: 'bg-blue-400', label: 'Scheduled' };
    case 'closed':
      return { bg: 'bg-slate-500/15', text: 'text-slate-400', dot: 'bg-slate-400', label: 'Closed' };
    case 'force_closed':
      return { bg: 'bg-red-500/15', text: 'text-red-400', dot: 'bg-red-400', label: 'Force Closed' };
    case 'draft':
      return { bg: 'bg-slate-500/15', text: 'text-slate-500', dot: 'bg-slate-500', label: 'Draft' };
    default:
      return { bg: 'bg-slate-500/15', text: 'text-slate-400', dot: 'bg-slate-400', label: status };
  }
}

/** Return rank badge classes: L1=gold, L2=silver, L3=bronze, rest=default */
export function rankStyle(label) {
  switch (label) {
    case 'L1': return 'bg-amber-400/20 text-amber-300 border border-amber-400/40';
    case 'L2': return 'bg-slate-400/20 text-slate-300 border border-slate-400/40';
    case 'L3': return 'bg-orange-700/20 text-orange-400 border border-orange-700/40';
    default:   return 'bg-slate-800 text-slate-400 border border-slate-700';
  }
}
