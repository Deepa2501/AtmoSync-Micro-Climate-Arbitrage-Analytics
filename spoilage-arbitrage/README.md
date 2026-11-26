# Spoilage Arbitrage

Part of the AtmoSync - Micro-Climate Arbitrage Analytics project. This module covers simulation, spoilage analysis and arbitrage opportunity detection.

## Structure
```text
spoilage-arbitrage/
├── analytics/     # spoilage scoring, regional price analysis, opportunity detection
├── data/          # avocado.csv (Kaggle / Hass Avocado Board)
├── dbt/           # data transformation workflows
├── docker/        # Kafka + Kafka UI
├── docs/          # data contract, spoilage-arbitrage-analysis.md
├── outputs/       # sample results (seed 42)
├── scripts/       # load_reference_data.py (Snowflake)
├── simulator/     # producer.py (IoT simulator with fault injection)
└── tests/         # pytest suite for analytics
```

## Run the analysis (no Kafka or Snowflake needed)
```bash
cd spoilage-arbitrage
pip install -r requirements-analytics.txt
python simulator/producer.py --dry-run --ticks 48 --interval 0 --seed 42 > outputs/sample_readings.jsonl 2> outputs/sample_truth.txt
python -m analytics.sample_data --readings outputs/sample_readings.jsonl --out outputs/sample_shipments.csv
python -m analytics.run_analysis --readings outputs/sample_readings.jsonl \
    --shipments outputs/sample_shipments.csv --prices data/avocado.csv \
    --truth outputs/sample_truth.txt --out outputs
python -m pytest tests -q
```

## Outputs (`outputs/`)
| File | Content |
|---|---|
| `container_risk_scores.csv` | indicators, score components, risk level per container |
| `regional_price_summary.csv` | per-market price level, volatility, gap vs mean |
| `price_gap_pairs.csv` | largest price gaps between market pairs |
| `arbitrage_opportunities.csv` | best alternative market per container and opportunity type |
| `sensitivity.csv` | opportunity counts under different assumptions |
| `evaluation_vs_injected_faults.csv` | flags vs the simulator's injected faults |

## Assumptions and limitations
All thresholds, the Q10 decay model and the shelf life are assumptions (`analytics/config.py`), not calibrated values. Prices are historical retail averages (to March 2018). Results are indicative screening output, not verified spoilage or profit. Details: `docs/spoilage-arbitrage-analysis.md`.
