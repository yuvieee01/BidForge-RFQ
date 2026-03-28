import { useEffect, useState } from 'react';
import { formatCountdown, secondsUntil } from '../utils/formatters';
import { useServerTime } from '../hooks/useServerTime';

/**
 * CountdownTimer
 * Props:
 *   targetTime — ISO string of the close time
 *   label      — e.g. "Closes in" / "Force closes in"
 *   urgent     — boolean, show red when < 5 min
 *   extended   — boolean, show amber pulse if extended
 */
export default function CountdownTimer({ targetTime, label = 'Closes in', urgent = false, extended = false }) {
  const now = useServerTime();
  const secs = secondsUntil(targetTime, now);
  const isUrgent = urgent && secs < 300; // < 5 min
  const isDone = secs === 0;

  return (
    <div className="flex flex-col items-center gap-1">
      <span className="text-xs text-slate-500 uppercase tracking-widest">{label}</span>
      <span
        className={`text-2xl font-mono font-bold tabular-nums transition-colors duration-300
          ${isDone ? 'text-slate-500' : isUrgent ? 'text-red-400 animate-pulse' : extended ? 'text-amber-400' : 'text-emerald-400'}`}
      >
        {isDone ? 'CLOSED' : formatCountdown(secs)}
      </span>
      {extended && !isDone && (
        <span className="text-xs text-amber-500 font-medium animate-pulse">⚡ Extended</span>
      )}
    </div>
  );
}
