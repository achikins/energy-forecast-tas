import { useState, useEffect } from "react";
import { fetchHistorical } from "../api/energyApi";

export function useHistoricalData(params = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Re-fetch whenever params change (limit, start, end)
  const paramsKey = JSON.stringify(params);

  const load = (overrideParams) => {
    setLoading(true);
    setError(null);
    fetchHistorical(overrideParams ?? params)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [paramsKey]);

  return { data, loading, error, refetch: () => load() };
}
