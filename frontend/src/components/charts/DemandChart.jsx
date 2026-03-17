/**
 * DemandChart — renders historical demand (solid blue) and forecast (dashed green)
 * on a shared time axis using Recharts.
 *
 * The forecast confidence band is shown as a shaded area between
 * the lower and upper bounds.
 */

import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import LoadingSpinner from "../common/LoadingSpinner";
import ErrorBanner from "../common/ErrorBanner";

/** Format ISO timestamp for a compact x-axis label */
function fmtAxisLabel(ts) {
  const d = new Date(ts);
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, "0")}:00`;
}

/** Custom tooltip */
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "10px 14px",
        fontSize: 12,
      }}
    >
      <div style={{ color: "var(--text-secondary)", marginBottom: 6 }}>{label}</div>
      {payload.map((entry) => (
        <div key={entry.name} style={{ color: entry.color ?? "var(--text-primary)", marginBottom: 2 }}>
          {entry.name}: <strong>{entry.value != null ? `${Number(entry.value).toFixed(0)} MW` : "—"}</strong>
        </div>
      ))}
    </div>
  );
}

/**
 * Merge historical and forecast arrays into a single chart data array.
 * Points are identified by their `source` field ("historical" | "forecast").
 */
function mergeChartData(historical, forecast) {
  const hist = (historical?.data ?? []).map((d) => ({
    ts: d.timestamp,
    historical: d.demand_mw,
    forecast: null,
    lower: null,
    upper: null,
  }));

  // Add a bridge point: last historical value is also the forecast start
  const lastHist = hist[hist.length - 1];
  const fc = (forecast?.data ?? []).map((d, i) => ({
    ts: d.timestamp,
    historical: i === 0 && lastHist ? lastHist.historical : null,
    forecast: d.predicted_mw,
    lower: d.lower_bound,
    upper: d.upper_bound,
  }));

  return [...hist, ...fc];
}

export default function DemandChart({
  historicalData,
  forecastData,
  historicalLoading,
  forecastLoading,
  historicalError,
  forecastError,
  onRetry,
}) {
  const loading = historicalLoading || forecastLoading;
  const error = historicalError || forecastError;

  if (loading) return <LoadingSpinner message="Loading chart data..." />;
  if (error) return <ErrorBanner message={error} onRetry={onRetry} />;

  const chartData = mergeChartData(historicalData, forecastData);

  // Find the timestamp where forecast begins (for the reference line)
  const forecastStart = forecastData?.data?.[0]?.ts ?? null;

  // Only label every Nth tick to avoid crowding
  const tickInterval = Math.max(1, Math.floor(chartData.length / 12));

  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />

        <XAxis
          dataKey="ts"
          tickFormatter={fmtAxisLabel}
          interval={tickInterval}
          tick={{ fill: "var(--text-muted)", fontSize: 11 }}
          axisLine={{ stroke: "var(--border)" }}
          tickLine={false}
        />

        <YAxis
          tickFormatter={(v) => `${v} MW`}
          tick={{ fill: "var(--text-muted)", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          width={72}
        />

        <Tooltip content={<CustomTooltip />} />

        {/* Confidence band */}
        <Area
          type="monotone"
          dataKey="upper"
          stroke="none"
          fill="var(--chart-band)"
          legendType="none"
          name="Upper bound"
          connectNulls
        />
        <Area
          type="monotone"
          dataKey="lower"
          stroke="none"
          fill="var(--bg-primary)" /* fills downward, masking the band below lower */
          legendType="none"
          name="Lower bound"
          connectNulls
        />

        {/* Historical line */}
        <Line
          type="monotone"
          dataKey="historical"
          stroke="var(--chart-historical)"
          strokeWidth={2}
          dot={false}
          name="Historical"
          connectNulls
        />

        {/* Forecast line */}
        <Line
          type="monotone"
          dataKey="forecast"
          stroke="var(--chart-forecast)"
          strokeWidth={2}
          strokeDasharray="6 3"
          dot={false}
          name="Forecast"
          connectNulls
        />

        {/* Vertical divider between historical and forecast */}
        {forecastStart && (
          <ReferenceLine
            x={forecastStart}
            stroke="var(--text-muted)"
            strokeDasharray="4 4"
            label={{ value: "Now", fill: "var(--text-muted)", fontSize: 11, position: "top" }}
          />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
