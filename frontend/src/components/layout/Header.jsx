import { useState } from "react";
import AboutModal from "./AboutModal";

export default function Header({ onRefresh, refreshing }) {
  const [showAbout, setShowAbout] = useState(false);

  return (
    <>
      <header className="header">
        <div className="header-brand">
          {/* Logo */}
          <div className="header-logo">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
          </div>
          <div>
            <div className="header-title">Energy Demand Forecasting</div>
            <div className="header-subtitle">Decision Support System · Tasmania</div>
          </div>
        </div>

        <div className="header-controls">
          {/* Data source badge — honest about synthetic data */}
          <span className="data-source-badge" title="Dataset is synthetic, modelled on real AEMO NEM structure for TAS1">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 5 }}>
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            Synthetic · AEMO structure
          </span>

          <span className="region-badge">TAS1 · NEM</span>

          <button
            className={`refresh-btn ${refreshing ? "refresh-btn--spinning" : ""}`}
            onClick={onRefresh}
            disabled={refreshing}
            title="Refresh all data"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            {refreshing ? "Loading…" : "Refresh"}
          </button>

        </div>
      </header>

      {showAbout && <AboutModal onClose={() => setShowAbout(false)} />}
    </>
  );
}
