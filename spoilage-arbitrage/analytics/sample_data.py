"""Generate SYNTHETIC demo shipments (container -> origin hub, planned market).

The current simulator emits ship routes (Rotterdam, Hamburg, ...) that are not
in the 16-market price table, so demo shipments are assigned here with a
fixed seed. This is an assumption for testing, not real routing data.
"""
import argparse
import random

import pandas as pd

from . import config as C


def make_shipments(container_ids, seed=7):
    rng = random.Random(seed)
    origins = list(C.ORIGINS_REF)
    markets = [m[0] for m in C.MARKETS_REF]
    rows = [{"container_id": cid, "origin": rng.choice(origins),
             "planned_market": rng.choice(markets),
             "progress": round(rng.uniform(0.15, 0.6), 2)} for cid in container_ids]
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--readings", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    ids = sorted(pd.read_json(a.readings, lines=True)["container_id"].unique())
    make_shipments(ids, a.seed).to_csv(a.out, index=False)
    print(f"wrote {len(ids)} shipments to {a.out}")
