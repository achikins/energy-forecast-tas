/**
 * API client — single integration boundary between the UI and the FastAPI backend.
 * All endpoint URLs and response shapes are defined here.
 * If the backend URL or contract changes, only this file needs updating.
 */

const BASE = "/api/v1";

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * Fetch historical demand data.
 * @param {object} params
 * @param {string} [params.start]  ISO date string
 * @param {string} [params.end]    ISO date string
 * @param {number} [params.limit]  Max records (default 168)
 */
export function fetchHistorical({ start, end, limit = 168 } = {}) {
  const qs = new URLSearchParams();
  if (start) qs.set("start", start);
  if (end) qs.set("end", end);
  qs.set("limit", limit);
  return get(`/historical?${qs}`);
}

/**
 * Fetch demand forecast.
 * @param {number} periods  Hours to forecast ahead (default 48)
 */
export function fetchForecast(periods = 48) {
  return get(`/forecast?periods=${periods}`);
}

/**
 * Fetch analytical insights.
 * @param {number} hours  Analysis window in hours (default 168)
 */
export function fetchInsights(hours = 168) {
  return get(`/insights?hours=${hours}`);
}

/**
 * Fetch the Energy Decision Layer — best usage windows and peak generation hours.
 */
export function fetchDecision() {
  return get("/decision");
}
