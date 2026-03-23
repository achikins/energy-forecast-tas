/**
 * AboutModal — slide-up overlay explaining the project and its author.
 * Triggered from the header "About" button.
 */

const STACK = [
  { label: "Backend",       value: "Python · FastAPI" },
  { label: "Forecasting",   value: "Holt-Winters Exponential Smoothing" },
  { label: "Frontend",      value: "React · Vite" },
  { label: "Charts",        value: "Recharts" },
  { label: "Map",           value: "Mapbox GL JS" },
  { label: "Data",          value: "Synthetic · AEMO NEM TAS1 structure" },
  { label: "Deployed on",   value: "Render (API) · Vercel (UI)" },
];

export default function AboutModal({ onClose }) {
  return (
    /* Backdrop */
    <div className="modal-backdrop" onClick={onClose}>
      {/* Panel — stop clicks propagating to backdrop */}
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>

        {/* Close button */}
        <button className="modal-close" onClick={onClose} aria-label="Close">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>

        {/* Avatar + name */}
        <div className="about-hero">
          <div className="about-avatar">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="8" r="4"/><path d="M6 20v-2a6 6 0 0 1 12 0v2"/>
            </svg>
          </div>
          <div>
            <div className="about-name">Achintha Fernando</div>
            <div className="about-role">Graduate Engineer · Hydro Tasmania applicant</div>
          </div>
        </div>

        {/* Project description */}
        <p className="about-desc">
          Built as a portfolio project for the <strong>Hydro Tasmania graduate role application</strong>.
          This system demonstrates end-to-end engineering thinking — from data ingestion and
          time-series forecasting through to a production-deployed decision support interface
          modelled on real-world energy grid operations.
        </p>

        {/* Data source note */}
        <div className="about-data-note">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, marginTop: 1 }}>
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>
            Demand data is <strong>synthetic</strong>, generated to match real AEMO NEM TAS1 patterns —
            seasonal variation, daily load profile, weekend reduction, and random industrial spikes.
            The data structure mirrors what AEMO publishes at <strong>nemweb.com.au</strong>.
          </span>
        </div>

        {/* Tech stack */}
        <div className="about-section-title">Tech Stack</div>
        <div className="about-stack">
          {STACK.map(({ label, value }) => (
            <div className="about-stack-row" key={label}>
              <span className="about-stack-key">{label}</span>
              <span className="about-stack-val">{value}</span>
            </div>
          ))}
        </div>

        {/* Links */}
        <div className="about-links">
          <a
            href="https://github.com/achikins"
            target="_blank"
            rel="noreferrer"
            className="about-link"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/>
            </svg>
            GitHub
          </a>
          <a
            href="https://www.linkedin.com/in/achintha-fernando-59697524b/"
            target="_blank"
            rel="noreferrer"
            className="about-link"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/>
              <rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/>
            </svg>
            LinkedIn
          </a>
          <a
            href="https://github.com/achikins/energy-forecast-tas"
            target="_blank"
            rel="noreferrer"
            className="about-link about-link--secondary"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            </svg>
            Source Code
          </a>
        </div>

      </div>
    </div>
  );
}
