/**
 * useServerTime.js
 * Syncs a server-time offset on login so countdown timers don't drift.
 * Usage: const now = useServerTime() → returns current server-synced Date.
 */
import { useState, useEffect, useRef } from 'react';

// Module-level offset (ms) — server time minus local time at last sync
let serverOffset = 0;

export function setServerTimeOffset(serverTimeIso) {
  const serverMs = new Date(serverTimeIso).getTime();
  const localMs = Date.now();
  serverOffset = serverMs - localMs;
}

export function getServerNow() {
  return new Date(Date.now() + serverOffset);
}

/**
 * Hook: returns a ticking Date object synced to server time.
 * Updates every second.
 */
export function useServerTime() {
  const [now, setNow] = useState(getServerNow);

  useEffect(() => {
    const id = setInterval(() => setNow(getServerNow()), 1000);
    return () => clearInterval(id);
  }, []);

  return now;
}
