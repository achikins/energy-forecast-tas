import InsightCard from "./InsightCard";
import LoadingSpinner from "../common/LoadingSpinner";
import ErrorBanner from "../common/ErrorBanner";

function formatMW(val) {
  return val != null ? val.toLocaleString(undefined, { maximumFractionDigits: 0 }) : "—";
}

function TrendPill({ trend, changePct }) {
  const classes = {
    rising: "trend-pill trend-rising",
    falling: "trend-pill trend-falling",
    stable: "trend-pill trend-stable",
  };
  const icons = { rising: "↑", falling: "↓", stable: "→" };
  return (
    <span className={classes[trend] ?? "trend-pill trend-stable"}>
      {icons[trend]} {Math.abs(changePct).toFixed(1)}%
    </span>
  );
}

export default function InsightsPanel({ data, loading, error, onRetry }) {
  if (loading) return <LoadingSpinner message="Computing insights..." />;
  if (error) return <ErrorBanner message={error} onRetry={onRetry} />;
  if (!data) return null;

  return (
    <div>
      {/* Narrative summary */}
      <div className="summary-box">
        <strong>Analysis Summary · </strong>
        {data.summary_text}
      </div>

      {/* Key metric cards */}
      <div className="insights-grid">
        <InsightCard
          label="Average Demand"
          value={formatMW(data.average_demand_mw)}
          unit="MW"
          meta="7-day rolling window"
          accent="var(--accent-blue)"
        />
        <InsightCard
          label="Peak Demand"
          value={formatMW(data.peak_demand_mw)}
          unit="MW"
          meta={data.peak_timestamp}
          accent="var(--accent-amber)"
        />
        <InsightCard
          label="Minimum Demand"
          value={formatMW(data.min_demand_mw)}
          unit="MW"
          meta={data.min_timestamp}
          accent="var(--accent-purple)"
        />
        <InsightCard
          label="Demand Trend"
          value={<TrendPill trend={data.demand_trend} changePct={data.trend_change_pct} />}
          meta={`${data.demand_trend.charAt(0).toUpperCase() + data.demand_trend.slice(1)} vs prior period`}
          accent={
            data.demand_trend === "rising"
              ? "var(--accent-red)"
              : data.demand_trend === "falling"
              ? "var(--accent-green)"
              : "var(--text-muted)"
          }
        />
        <InsightCard
          label="Anomalies Detected"
          value={data.anomalies.length}
          unit=""
          meta="Unusual demand readings"
          accent={data.anomalies.length > 0 ? "var(--accent-red)" : "var(--accent-green)"}
        />
      </div>
    </div>
  );
}
