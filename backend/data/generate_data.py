"""
Script to generate realistic synthetic energy demand data for Tasmania.
Run once: python data/generate_data.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

START = datetime(2023, 1, 1)
PERIODS = 365 * 24  # one year of hourly data

timestamps = [START + timedelta(hours=i) for i in range(PERIODS)]

def base_demand(dt: datetime) -> float:
    """Simulate realistic demand with daily, weekly, and seasonal patterns."""
    hour = dt.hour
    month = dt.month
    weekday = dt.weekday()  # 0=Monday, 6=Sunday

    # Daily profile: morning ramp, midday plateau, evening peak
    if 0 <= hour < 6:
        daily = 800 + hour * 30
    elif 6 <= hour < 9:
        daily = 980 + (hour - 6) * 80
    elif 9 <= hour < 17:
        daily = 1200 + np.sin((hour - 9) / 8 * np.pi) * 100
    elif 17 <= hour < 21:
        daily = 1300 + (hour - 17) * 40
    else:
        daily = 1460 - (hour - 21) * 100

    # Weekend reduction (~15%)
    weekend_factor = 0.85 if weekday >= 5 else 1.0

    # Seasonal variation: higher in winter (Tasmania is Southern Hemisphere)
    # Peak in June/July, trough in January
    seasonal = 1.0 + 0.25 * np.cos((month - 7) / 12 * 2 * np.pi)

    return daily * weekend_factor * seasonal


demand_values = []
for ts in timestamps:
    base = base_demand(ts)
    # Add realistic noise
    noise = np.random.normal(0, 30)
    # Occasional demand spikes (industrial events)
    spike = np.random.choice([0, 200], p=[0.99, 0.01])
    demand_values.append(max(600, base + noise + spike))

df = pd.DataFrame({
    "timestamp": [ts.strftime("%Y-%m-%d %H:%M:%S") for ts in timestamps],
    "demand_mw": [round(v, 2) for v in demand_values],
    "region": "TAS",
})

output_path = "energy_demand.csv"
df.to_csv(output_path, index=False)
print(f"Generated {len(df)} rows -> {output_path}")
