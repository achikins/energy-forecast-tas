/**
 * useServerWake — shows a "waking up server" banner when any request
 * is still loading after DELAY_MS. Hides automatically once loading stops.
 */

import { useEffect, useState } from "react";

const DELAY_MS = 3000;

export function useServerWake(isLoading) {
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    if (!isLoading) {
      setShowBanner(false);
      return;
    }
    const timer = setTimeout(() => setShowBanner(true), DELAY_MS);
    return () => clearTimeout(timer);
  }, [isLoading]);

  return showBanner;
}
