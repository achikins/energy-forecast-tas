import { useState, useEffect } from "react";
import { fetchForecast } from "../api/energyApi";

export function useForecastData(periods = 48) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = () => {
    setLoading(true);
    setError(null);
    fetchForecast(periods)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, [periods]);

  return { data, loading, error, refetch: load };
}
