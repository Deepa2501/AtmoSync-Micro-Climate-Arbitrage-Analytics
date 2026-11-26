"""Run spoilage scoring + regional price analysis + opportunity detection.

From the spoilage-arbitrage/ folder:
  python -m analytics.run_analysis --readings outputs/sample_readings.jsonl \
      --shipments outputs/sample_shipments.csv --prices data/avocado.csv \
      --truth outputs/sample_truth.txt --out outputs
"""
import argparse
import re
from pathlib import Path

import pandas as pd

from . import arbitrage as A
from . import spoilage as S


def load_readings(path):
    df = pd.read_json(path, lines=True)
    return df.sort_values(["container_id"], kind="stable").reset_index(drop=True)


def parse_truth(path):
    """Parse '[truth] CNT-0001 A->B transit=300h fault=temp_drift' lines."""
    truth = {}
    for line in Path(path).read_text().splitlines():
        m = re.match(r"\[truth\] (\S+) .* fault=(\S+)", line)
        if m:
            truth[m.group(1)] = None if m.group(2) == "None" else m.group(2)
    return truth


def evaluate(scores, truth, min_level):
    """Confusion counts for 'flagged = risk level >= min_level' vs injected faults."""
    order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    tp = fp = fn = tn = 0
    for _, r in scores.iterrows():
        actual = truth.get(r["container_id"]) is not None
        flagged = order[r["risk_level"]] >= order[min_level]
        tp += actual and flagged
        fp += (not actual) and flagged
        fn += actual and (not flagged)
        tn += (not actual) and (not flagged)
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    return {"flag_threshold": f">={min_level}", "tp": int(tp), "fp": int(fp),
            "fn": int(fn), "tn": int(tn), "precision": prec, "recall": rec}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--readings", required=True)
    ap.add_argument("--shipments", required=True)
    ap.add_argument("--prices", required=True)
    ap.add_argument("--truth")
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--type", default="conventional")
    ap.add_argument("--step-hours", type=float, default=None)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    scores = S.score_containers(load_readings(a.readings), a.step_hours)
    scores.round(3).to_csv(out / "container_risk_scores.csv", index=False)

    prices = A.load_prices(a.prices)
    summary = A.regional_price_summary(prices, a.type)
    summary.to_csv(out / "regional_price_summary.csv", index=False)
    pbm = A.current_prices(prices, a.type)
    A.price_gap_pairs(pbm).to_csv(out / "price_gap_pairs.csv", index=False)

    ships = pd.read_csv(a.shipments)
    opp = A.detect_opportunities(scores, ships, pbm)
    opp.to_csv(out / "arbitrage_opportunities.csv", index=False)
    A.sensitivity(scores, ships, pbm).to_csv(out / "sensitivity.csv", index=False)

    print("Risk levels:", scores["risk_level"].value_counts().to_dict())
    print("Opportunities:", opp["opportunity"].value_counts().to_dict())
    print(f"Prices as of {summary['as_of'].iloc[0]} (historical data, not current)")
    if a.truth:
        truth = parse_truth(a.truth)
        ev = pd.DataFrame([evaluate(scores, truth, lvl) for lvl in ("MEDIUM", "HIGH")])
        ev.round(3).to_csv(out / "evaluation_vs_injected_faults.csv", index=False)
        print(ev.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
