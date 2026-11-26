# Spoilage analysis and arbitrage opportunity detection

Status: preliminary prototype. Every number below is either (a) computed from the
simulator or the Kaggle price file, or (b) an ASSUMPTION listed here. Nothing in this
document is verified real-world spoilage or profit.

## 1. Data and components inspected
| Component | What it provides | Notes |
|---|---|---|
| `simulator/producer.py` | 20 reefer containers, hourly readings: temperature_c, humidity_pct, vibration_g, lat/lon, origin, destination | ~25% of voyages get an injected fault (`temp_drift` or `humidity_spike`); ground truth is printed to stderr as `[truth]` lines |
| `data/avocado.csv` (Kaggle / Hass Avocado Board) | weekly average price per region, conventional and organic, 2015-12 to 2018-03 | 16 reference markets used; prices are retail averages per avocado, historical |
| `scripts/load_reference_data.py` | MARKETS (16 US cities, lat/lon), ORIGINS (Uruapan, Lazaro Cardenas, Pharr) | duplicated in `analytics/config.py`; keep in sync |

Limitations found while inspecting:
- Simulator `event_ts` is wall-clock time, not simulated time. The analytics therefore assume evenly spaced readings (`STEP_HOURS`, default 1.0 = `--sim-minutes 60`).
- Simulator routes are ship routes (Rotterdam, Hamburg, Los Angeles, New York), not the Mexico-to-US truck routes with real prices. Demo shipments are assigned synthetically (`analytics/sample_data.py`).
- `docs/data-contract.md` on the `Suyash-pandey` branch is empty.

## 2. Environmental factors considered
Temperature (level, time out of band, warming trend) and relative humidity (level out of band) are used in the score. Vibration is available but not scored. Atmospheric/outside weather is not used.

## 3. Spoilage risk indicators (`analytics/spoilage.py`)
Per reading: temperature deviation outside 4-8 C, humidity deviation outside 85-95 %, relative decay rate = Q10^((T - 6)/10) with Q10 = 2.
Per container: recent (last 6 readings) temperature/humidity, share of readings out of band, warming slope (C/h, least squares), degree-hours above 8 C, recent decay rate.

## 4. Rule-based risk score (0-100)
| Component | Max points | Rule |
|---|---|---|
| Temperature level | 50 | recent deviation outside band / 6 C, capped at 1 |
| Temperature duration | 15 | share of readings outside band |
| Temperature trend | 10 | slope 0.05 C/h scores 0, 0.30 C/h scores full |
| Humidity level | 25 | recent deviation outside band / 3 %, capped at 1 |

Levels: LOW < 25, MEDIUM 25-49.9, HIGH 50-74.9, CRITICAL >= 75. Humidity alone can reach at most 25 points (MEDIUM) by design.
The score is a relative risk indicator. It is not a prediction of spoilage or shelf life.

## 5. Regional price analysis (`analytics/arbitrage.py`)
`regional_price_summary` gives per-market mean, std, min, max over the last 4 weeks and the gap versus the 16-market mean. `price_gap_pairs` ranks market pairs by absolute and percent gap with their distance.

## 6. Opportunity detection
For each container: position = straight line from origin hub to planned market at `progress`. For every other market:
`net = price x (1 - min(1, decay_rate x hours / base_shelf_life)) x (1 - detour_penalty)`; advantage % = net_alt / net_planned - 1.
- `RISK_DRIVEN`: risk HIGH/CRITICAL, alternative arrives sooner, advantage >= 5 %.
- `PRICE_SPREAD_ONLY`: advantage >= 25 % (higher bar because freight, handling and market capacity are not modelled).
- `NONE` otherwise. Alternatives more than 1,500 km farther than the plan are excluded.

## 7. Assumptions (all in `analytics/config.py`)
Temperature band 4-8 C, humidity band 85-95 %, Q10 = 2, reference 6 C, base shelf life 504 h at 6 C, truck speed 70 km/h on straight-line distance, detour penalty 1 % per 1,000 km extra, thresholds above. None is calibrated; replace with values from a postharvest reference or domain expert before drawing conclusions.

## 8. Sample results (simulator seed 42, 48 hourly readings x 20 containers)
Files are in `outputs/`.
- Risk levels: 18 LOW, 2 HIGH (CNT-0001, CNT-0002).
- Injected faults (ground truth): CNT-0001 and CNT-0002 `temp_drift`, CNT-0016 `humidity_spike`. Flagged at MEDIUM or above: 2 of 3 (precision 1.0, recall 0.67, tiny sample). The humidity spike was missed: the simulator pushes humidity to about 97 %, only about 2 points above the assumed 95 % limit, and humidity alone caps at 25 points.
- Opportunities: 1 RISK_DRIVEN (CNT-0001, Phoenix to Houston, +16.5 % quality-adjusted, indicative), 8 PRICE_SPREAD_ONLY, 11 NONE.
- Price data: as of 2018-03-25, conventional avocados. Market means range from about 44 % below to 31 % above the 16-market mean (Phoenix lowest, Chicago highest).
- `sensitivity.csv` shows how counts change with shelf life (72-504 h) and the price-only bar. Risk-driven counts stay at 1-2 because, on truck-length trips, the extra decay from a few hours difference is small compared with regional price gaps. The spoilage effect should matter more on the 250-300 h ship voyages the current simulator produces.

## 9. Not claimed
No profit, margin or shelf-life figure here is verified. Prices are historical retail averages, costs are not modelled, and all spoilage parameters are assumptions.

## 10. Next steps
Confirm bands, Q10 and shelf life with the mentor; make the simulator emit simulated timestamps and Mexico-to-US routes; add freight cost and market volume; port the scoring to a dbt model once the logic is agreed.
