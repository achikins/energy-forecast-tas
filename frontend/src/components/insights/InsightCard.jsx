/**
 * InsightCard — displays a single key metric with label, value, and optional metadata.
 *
 * Props:
 *   label    string   — short title (e.g. "Peak Demand")
 *   value    string   — formatted primary value (e.g. "1,450")
 *   unit     string   — unit suffix (e.g. "MW")
 *   meta     string   — secondary line (e.g. timestamp or trend text)
 *   accent   string   — CSS color var name or hex for left border accent
 */
export default function InsightCard({ label, value, unit, meta, accent }) {
  const borderColor = accent ?? "var(--accent-blue)";

  return (
    <div
      className="insight-card"
      style={{ borderLeftWidth: 3, borderLeftColor: borderColor }}
    >
      <div className="insight-card-label">{label}</div>
      <div className="insight-card-value">
        {value}
        {unit && <span>{unit}</span>}
      </div>
      {meta && <div className="insight-card-meta">{meta}</div>}
    </div>
  );
}
