import { useState } from "react";

import Header from "../components/layout/Header";
import DemandChart from "../components/charts/DemandChart";
import InsightsPanel from "../components/insights/InsightsPanel";
import DecisionPanel from "../components/decision/DecisionPanel";
import LoadingSpinner from "../components/common/LoadingSpinner";
import TasmaniaMap from "../components/map/TasmaniaMap";

import { useHistoricalData } from "../hooks/useHistoricalData";
import { useForecastData } from "../hooks/useForecastData";
import { useInsights } from "../hooks/useInsights";
import { useDecision } from "../hooks/useDecision";

// ── Control options ──────────────────────────────────────────────────────────

const HISTORY_OPTIONS = [
  { label: "24h",  hours: 24 },
  { label: "3d",   hours: 72 },
  { label: "7d",   hours: 168 },
  { label: "14d",  hours: 336 },
  { label: "30d",  hours: 720 },
];

const FORECAST_OPTIONS = [
  { label: "12h",  periods: 12 },
  { label: "24h",  periods: 24 },
  { label: "48h",  periods: 48 },
  { label: "7d",   periods: 168 },
];

// ── Small reusable components ────────────────────────────────────────────────

function SegmentedControl({ options, value, onChange }) {
  return (
    <div className="segmented-control">
      {options.map((opt) => (
        <button
          key={opt.label}
          className={`seg-btn ${value === opt.value ? "seg-btn--active" : ""}`}
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

function IconButton({ onClick, loading, title, children }) {
  return (
    <button
      className={`icon-btn ${loading ? "icon-btn--spinning" : ""}`}
      onClick={onClick}
      disabled={loading}
      title={title}
    >
      {children}
    </button>
  );
}

function formatMW(val) {
  return val != null ? val.toLocaleString(undefined, { maximumFractionDigits: 0 }) : "—";
}

// ── Dashboard ────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const [histHours, setHistHours]       = useState(168);   // historical window
  const [forecastPeriods, setForecast]  = useState(48);    // forecast horizon
  const [insightsHours, setInsights]    = useState(168);   // insights window

  const historical = useHistoricalData({ limit: histHours });
  const forecast   = useForecastData(forecastPeriods);
  const insights   = useInsights(insightsHours);
  const decision   = useDecision();

  const anyLoading = historical.loading || forecast.loading || insights.loading;

  function refreshAll() {
    historical.refetch();
    forecast.refetch();
    insights.refetch();
    decision.refetch();
  }

  return (
    <div className="layout">
      <Header onRefresh={refreshAll} refreshing={anyLoading} />

      <main className="main-content">

        {/* ── Controls bar ── */}
        <div className="controls-bar">
          <div className="controls-group">
            <span className="controls-label">History</span>
            <SegmentedControl
              options={HISTORY_OPTIONS.map((o) => ({ label: o.label, value: o.hours }))}
              value={histHours}
              onChange={(v) => { setHistHours(v); setInsights(v); }}
            />
          </div>

          <div className="controls-group">
            <span className="controls-label">Forecast</span>
            <SegmentedControl
              options={FORECAST_OPTIONS.map((o) => ({ label: o.label, value: o.periods }))}
              value={forecastPeriods}
              onChange={setForecast}
            />
          </div>

          <IconButton onClick={refreshAll} loading={anyLoading} title="Refresh all data">
            ↻
          </IconButton>
        </div>

        {/* ── Insights cards ── */}
        <div className="section-header" style={{ marginTop: 4 }}>
          <span className="section-title">
            Demand Insights · Last {HISTORY_OPTIONS.find(o => o.hours === insightsHours)?.label ?? insightsHours + "h"}
          </span>
        </div>
        <InsightsPanel
          data={insights.data}
          loading={insights.loading}
          error={insights.error}
          onRetry={insights.refetch}
        />

        {/* ── Energy Decision Layer ── */}
        <div className="section-header" style={{ marginTop: 8 }}>
          <span className="section-title">Energy Decision Layer · Next 48h</span>
        </div>
        <div className="card" style={{ marginBottom: 24 }}>
          <DecisionPanel
            data={decision.data}
            loading={decision.loading}
            error={decision.error}
            onRetry={decision.refetch}
          />
        </div>

        {/* ── Chart ── */}
        <div className="chart-card">
          <div className="chart-header">
            <div>
              <div className="chart-title">Demand Overview</div>
              <div className="chart-subtitle">
                {HISTORY_OPTIONS.find(o => o.hours === histHours)?.label ?? histHours + "h"} historical
                &nbsp;+&nbsp;
                {FORECAST_OPTIONS.find(o => o.periods === forecastPeriods)?.label ?? forecastPeriods + "h"} forecast
                &nbsp;· 90% confidence band
              </div>
            </div>
            <div className="chart-legend">
              <div className="legend-item">
                <div className="legend-line" style={{ background: "var(--chart-historical)" }} />
                Historical
              </div>
              <div className="legend-item">
                <div className="legend-line legend-line-dashed" />
                Forecast
              </div>
              <div className="legend-item">
                <div style={{ width: 16, height: 10, background: "var(--chart-band)", borderRadius: 2 }} />
                90% CI
              </div>
            </div>
          </div>

          <DemandChart
            historicalData={historical.data}
            forecastData={forecast.data}
            historicalLoading={historical.loading}
            forecastLoading={forecast.loading}
            historicalError={historical.error}
            forecastError={forecast.error}
            onRetry={refreshAll}
          />
        </div>

        {/* ── Map ── */}
        <div className="section-header">
          <span className="section-title">Infrastructure Map · Tasmania</span>
        </div>
        <div style={{ marginBottom: 24 }}>
          <TasmaniaMap
            currentDemandMw={insights.data?.average_demand_mw ?? null}
            peakDemandMw={insights.data?.peak_demand_mw ?? null}
          />
        </div>

        {/* ── Lower grid: anomalies + peaks ── */}
        <div className="lower-grid">

          {/* Anomaly list */}
          <div className="card">
            <div className="section-header">
              <span className="section-title">Anomalies Detected</span>
              {!insights.loading && insights.data && (
                <span className={`count-badge ${insights.data.anomalies.length > 0 ? "count-badge--red" : "count-badge--green"}`}>
                  {insights.data.anomalies.length}
                </span>
              )}
            </div>
            {insights.loading ? (
              <LoadingSpinner message="Scanning for anomalies..." />
            ) : insights.data?.anomalies?.length > 0 ? (
              <div className="anomaly-list">
                {insights.data.anomalies.map((a, i) => (
                  <div className="anomaly-item" key={i}>
                    <span className="anomaly-ts">{a.timestamp}</span>
                    <span className="anomaly-desc">{a.description}</span>
                    <span className="anomaly-mw">{formatMW(a.demand_mw)} MW</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-state">No anomalies detected in the current window.</p>
            )}
          </div>

          {/* Top peak periods */}
          <div className="card">
            <div className="section-header">
              <span className="section-title">Top Peak Periods</span>
              {!insights.loading && insights.data && (
                <span className="count-badge count-badge--amber">
                  {insights.data.top_peak_periods.length}
                </span>
              )}
            </div>
            {insights.loading ? (
              <LoadingSpinner message="Finding peaks..." />
            ) : insights.data?.top_peak_periods?.length > 0 ? (
              <div className="anomaly-list">
                {insights.data.top_peak_periods.map((p, i) => (
                  <div
                    className="anomaly-item"
                    key={i}
                    style={{ borderColor: "rgba(251,191,36,0.2)", background: "rgba(251,191,36,0.04)" }}
                  >
                    <span className="anomaly-ts">{p.timestamp}</span>
                    <span style={{ color: "var(--accent-amber)", fontSize: 12, fontWeight: 500 }}>
                      {p.day_of_week} · {String(p.hour_of_day).padStart(2, "0")}:00
                    </span>
                    <span className="anomaly-mw">{formatMW(p.demand_mw)} MW</span>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        </div>

        {/* ── Footer ── */}
        <div className="page-footer">
          <span>Energy Demand Forecasting System · Tasmania · AEMO NEM Data</span>
          <span>Holt-Winters Exponential Smoothing · Seasonal Period 24h</span>
        </div>

      </main>
    </div>
  );
}
