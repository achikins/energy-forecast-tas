import { useState, useEffect } from "react";
import { fetchInsights } from "../api/energyApi";

export function useInsights(hours = 168) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = () => {
    setLoading(true);
    setError(null);
    fetchInsights(hours)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, [hours]);

  return { data, loading, error, refetch: load };
}
