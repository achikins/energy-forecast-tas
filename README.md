# Energy Demand Forecasting & Decision Support System

A production-style full-stack application for energy demand analysis and short-term forecasting, inspired by real-world grid operators like Hydro Tasmania.

## Architecture

```
┌─────────────────────────────────────────────┐
│              React + Vite (port 5173)        │
│  Dashboard → DemandChart + InsightsPanel     │
└───────────────────┬─────────────────────────┘
                    │ HTTP (proxied via Vite)
┌───────────────────▼─────────────────────────┐
│              FastAPI (port 8000)             │
│  /api/v1/historical  /forecast  /insights   │
└───────────────────┬─────────────────────────┘
                    │ pandas read_csv
┌───────────────────▼─────────────────────────┐
│         data/energy_demand.csv               │
│         8,760 hourly rows · 1 year · TAS    │
└─────────────────────────────────────────────┘
```

## Quick Start

### 1. Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate dataset (already included, run to regenerate)
python data/generate_data.py

# Start the API server
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

Open: http://localhost:5173

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/historical` | GET | Historical demand data (filterable by date range) |
| `/api/v1/forecast` | GET | Demand forecast for next N hours |
| `/api/v1/insights` | GET | Peak demand, anomalies, trend analysis |
| `/health` | GET | Liveness check |

### Query Parameters

**`/historical`**
- `start` — ISO date string (optional)
- `end` — ISO date string (optional)
- `limit` — max records, default 168 (7 days)

**`/forecast`**
- `periods` — hours ahead, default 48, max 168

**`/insights`**
- `hours` — analysis window, default 168 (7 days)

---

## Forecasting Method

**Holt-Winters Triple Exponential Smoothing** (additive trend + additive seasonality, period = 24 hours)

- Fitted on the most recent 30 days of hourly data
- Captures both intraday demand cycles and week-over-week trends
- Confidence bands are derived from residual standard deviation (90% CI, z = 1.645)
- No training infrastructure required — fits in < 1 second on 720 data points

---

## Project Structure

```
energy-forecast/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + CORS + startup
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── routers/             # HTTP layer only
│   │   │   ├── historical.py
│   │   │   ├── forecast.py
│   │   │   └── insights.py
│   │   ├── services/            # Business logic
│   │   │   ├── data_service.py
│   │   │   ├── forecast_service.py
│   │   │   └── insights_service.py
│   │   └── models/              # Pydantic response models
│   │       ├── demand.py
│   │       ├── forecast.py
│   │       └── insights.py
│   ├── data/
│   │   ├── energy_demand.csv    # 8,760 rows of synthetic hourly data
│   │   └── generate_data.py    # Regenerate dataset
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── api/energyApi.js     # Single API integration boundary
    │   ├── hooks/               # Data-fetching hooks (one per endpoint)
    │   ├── components/
    │   │   ├── charts/          # DemandChart (Recharts)
    │   │   ├── insights/        # InsightsPanel + InsightCard
    │   │   ├── layout/          # Header
    │   │   └── common/          # LoadingSpinner, ErrorBanner
    │   └── pages/Dashboard.jsx  # Main page
    ├── vite.config.js           # Dev proxy → backend
    └── package.json
```
