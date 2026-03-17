export default function Header({ onRefresh, refreshing }) {
  return (
    <header className="header">
      <div className="header-brand">
        <div className="header-logo">⚡</div>
        <div>
          <div className="header-title">Energy Demand Forecasting</div>
          <div className="header-subtitle">Decision Support System · Tasmania</div>
        </div>
      </div>

      <div className="header-controls">
        <span className="region-badge">TAS1 · NEM</span>
        <div className="status-indicator">
          <div className="status-dot" />
          AEMO Live Data
        </div>
        <button
          className={`refresh-btn ${refreshing ? "refresh-btn--spinning" : ""}`}
          onClick={onRefresh}
          disabled={refreshing}
          title="Refresh all data"
        >
          ↻ {refreshing ? "Loading…" : "Refresh"}
        </button>
      </div>
    </header>
  );
}
