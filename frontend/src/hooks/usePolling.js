/**
 * usePolling.js
 * Polls a fetch function every `intervalMs` milliseconds.
 * Stops polling when the component unmounts or when `active` is false.
 */
import { useEffect, useRef } from 'react';

export function usePolling(fetchFn, intervalMs = 5000, active = true) {
  const savedFn = useRef(fetchFn);

  useEffect(() => {
    savedFn.current = fetchFn;
  }, [fetchFn]);

  useEffect(() => {
    if (!active) return;

    // Fire immediately on mount
    savedFn.current();

    const id = setInterval(() => savedFn.current(), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs, active]);
}
