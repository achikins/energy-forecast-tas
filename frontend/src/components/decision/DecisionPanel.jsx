import LoadingSpinner from "../common/LoadingSpinner";
import ErrorBanner from "../common/ErrorBanner";

function ConfidencePill({ level }) {
  const styles = {
    high:   { bg: "rgba(52,211,153,0.12)",  color: "var(--accent-green)"  },
    medium: { bg: "rgba(251,191,36,0.12)",  color: "var(--accent-amber)"  },
    low:    { bg: "rgba(139,143,168,0.12)", color: "var(--text-secondary)" },
  };
  const s = styles[level] ?? styles.low;
  return (
    <span style={{
      background: s.bg, color: s.color,
      fontSize: 10, fontWeight: 700, padding: "2px 7px",
      borderRadius: 20, textTransform: "uppercase", letterSpacing: "0.07em",
    }}>
      {level}
    </span>
  );
}

function WindowCard({ icon, label, windowData, accentColor, metaKey }) {
  return (
    <div style={{
      display: "flex", flexDirection: "column", gap: 8,
      padding: "14px 16px",
      background: `color-mix(in srgb, ${accentColor} 6%, transparent)`,
      border: `1px solid color-mix(in srgb, ${accentColor} 20%, transparent)`,
      borderRadius: "var(--radius-sm)",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 2 }}>
        <span style={{ fontSize: 16 }}>{icon}</span>
        <span style={{ fontSize: 12, fontWeight: 700, color: "var(--text-secondary)",
          textTransform: "uppercase", letterSpacing: "0.07em" }}>
          {label}
        </span>
      </div>
      {windowData.map((w, i) => (
        <div key={i} style={{
          background: "var(--bg-primary)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-sm)",
          padding: "10px 14px",
        }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)",
              fontVariantNumeric: "tabular-nums" }}>
              {w.label}
            </span>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              {w.confidence && <ConfidencePill level={w.confidence} />}
              <span style={{ fontSize: 12, fontWeight: 600, color: accentColor,
                fontVariantNumeric: "tabular-nums" }}>
                ~{w[metaKey]?.toLocaleString(undefined, { maximumFractionDigits: 0 })} MW
              </span>
            </div>
          </div>
          <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.55, margin: 0 }}>
            {w.reason ?? w.note}
          </p>
        </div>
      ))}
    </div>
  );
}

export default function DecisionPanel({ data, loading, error, onRetry }) {
  if (loading) return <LoadingSpinner message="Computing energy decisions..." />;
  if (error)   return <ErrorBanner message={error} onRetry={onRetry} />;
  if (!data)   return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Advice banner */}
      <div className="summary-box" style={{
        borderColor: "rgba(52,211,153,0.25)",
        background: "rgba(52,211,153,0.05)",
        marginBottom: 0,
      }}>
        <strong style={{ color: "var(--accent-green)" }}>Decision · </strong>
        {data.advice}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {data.best_usage_windows?.length > 0 && (
          <WindowCard
            icon="⚡"
            label="Best time to use energy"
            windowData={data.best_usage_windows}
            accentColor="var(--accent-green)"
            metaKey="avg_demand_mw"
          />
        )}
        {data.peak_generation_windows?.length > 0 && (
          <WindowCard
            icon="🔋"
            label="Expected peak generation hours"
            windowData={data.peak_generation_windows}
            accentColor="var(--accent-amber)"
            metaKey="expected_demand_mw"
          />
        )}
      </div>

      <div style={{ fontSize: 11, color: "var(--text-muted)", textAlign: "right" }}>
        Generated {data.generated_at} · Based on 48-hour demand forecast
      </div>
    </div>
  );
}
