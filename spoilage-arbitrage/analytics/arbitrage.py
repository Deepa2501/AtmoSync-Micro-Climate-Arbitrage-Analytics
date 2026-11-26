"""Regional price analysis and preliminary arbitrage opportunity detection.

Prices come from the Hass Avocado Board weekly retail data (Kaggle),
which ends in March 2018: it demonstrates the method, it is NOT current.
Results are INDICATIVE. Freight, handling and contract costs are not
modelled beyond a crude detour penalty (see config.py).
"""
import math

import pandas as pd

from . import config as C

MARKET_BY_KEY = {m[1]: m for m in C.MARKETS_REF}
MARKET_COORDS = {m[0]: (m[2], m[3]) for m in C.MARKETS_REF}


def haversine_km(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 6371.0 * 2 * math.asin(math.sqrt(h))


# ---------------------------------------------------------------- prices ----
def load_prices(path):
    """Load avocado.csv, keep the 16 reference markets, add market name."""
    df = pd.read_csv(path)
    df = df.rename(columns={"Date": "price_date", "AveragePrice": "average_price",
                            "Total Volume": "total_volume", "region": "region_key"})
    df["price_date"] = pd.to_datetime(df["price_date"])
    df = df[df["region_key"].isin(MARKET_BY_KEY)].copy()
    df["market"] = df["region_key"].map(lambda k: MARKET_BY_KEY[k][0])
    return df[["price_date", "market", "type", "average_price", "total_volume"]]


def current_prices(prices, avocado_type="conventional", as_of=None, window_weeks=None):
    """Mean price per market over the last N weeks up to as_of (dict)."""
    weeks = window_weeks or C.PRICE_WINDOW_WEEKS
    p = prices[prices["type"] == avocado_type]
    as_of = pd.Timestamp(as_of) if as_of is not None else p["price_date"].max()
    start = as_of - pd.Timedelta(weeks=weeks)
    w = p[(p["price_date"] <= as_of) & (p["price_date"] > start)]
    return w.groupby("market")["average_price"].mean().to_dict()


def regional_price_summary(prices, avocado_type="conventional", as_of=None, window_weeks=None):
    """Per-market price level, spread vs. the 16-market mean and volatility."""
    weeks = window_weeks or C.PRICE_WINDOW_WEEKS
    p = prices[prices["type"] == avocado_type]
    as_of = pd.Timestamp(as_of) if as_of is not None else p["price_date"].max()
    w = p[(p["price_date"] <= as_of) & (p["price_date"] > as_of - pd.Timedelta(weeks=weeks))]
    g = w.groupby("market")["average_price"]
    s = pd.DataFrame({"mean_price": g.mean(), "std_price": g.std(),
                      "min_price": g.min(), "max_price": g.max(), "n_weeks": g.count()})
    overall = s["mean_price"].mean()
    s["vs_market_mean_pct"] = (s["mean_price"] / overall - 1) * 100
    s["as_of"] = as_of.date()
    return s.sort_values("mean_price", ascending=False).round(4).reset_index()


def price_gap_pairs(price_by_market, top_n=10):
    """Largest absolute price gaps between market pairs (dict -> DataFrame)."""
    names = sorted(price_by_market)
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            hi, lo = (a, b) if price_by_market[a] >= price_by_market[b] else (b, a)
            rows.append({"high_market": hi, "low_market": lo,
                         "gap": price_by_market[hi] - price_by_market[lo],
                         "gap_pct_of_low": (price_by_market[hi] / price_by_market[lo] - 1) * 100,
                         "distance_km": haversine_km(MARKET_COORDS[hi], MARKET_COORDS[lo])})
    return pd.DataFrame(rows).sort_values("gap", ascending=False).head(top_n).round(4).reset_index(drop=True)


# ---------------------------------------------------------- opportunities ----
def position_at(origin_name, planned_market, progress):
    """Straight-line position between origin hub and planned market."""
    o, d = C.ORIGINS_REF[origin_name], MARKET_COORDS[planned_market]
    f = min(1.0, max(0.0, progress))
    return (o[0] + (d[0] - o[0]) * f, o[1] + (d[1] - o[1]) * f)


def expected_loss_fraction(rate, hours, shelf_life_h=None):
    """Share of base shelf life consumed in transit (capped at 1.0)."""
    life = shelf_life_h or C.BASE_SHELF_LIFE_H
    return min(1.0, max(0.0, rate * hours / life))


def evaluate_alternatives(pos, planned_market, rate, price_by_market, shelf_life_h=None):
    """All alternative markets for one container, with quality-adjusted price."""
    d_plan = haversine_km(pos, MARKET_COORDS[planned_market])
    h_plan = d_plan / C.TRANSPORT_SPEED_KMH
    net_plan = price_by_market[planned_market] * (1 - expected_loss_fraction(rate, h_plan, shelf_life_h))
    rows = []
    for name, coords in MARKET_COORDS.items():
        if name == planned_market or name not in price_by_market:
            continue
        d = haversine_km(pos, coords)
        h = d / C.TRANSPORT_SPEED_KMH
        extra = d - d_plan
        penalty = max(0.0, extra) / 1000.0 * C.DETOUR_PENALTY_PCT_PER_1000KM / 100.0
        loss = expected_loss_fraction(rate, h, shelf_life_h)
        net = price_by_market[name] * (1 - loss) * (1 - penalty)
        adv = (net / net_plan - 1) * 100 if net_plan > 0 else float("inf")
        rows.append({"alt_market": name, "alt_price": price_by_market[name],
                     "distance_km": d, "extra_km": extra, "hours_to_alt": h,
                     "net_alt": net, "advantage_pct": adv,
                     "arrives_sooner": h < h_plan})
    return h_plan, net_plan, pd.DataFrame(rows)


def detect_opportunities(risk_df, shipments, price_by_market, shelf_life_h=None,
                         min_adv=None, price_only_min_adv=None):
    """Best alternative market per container.

    risk_df: output of spoilage.score_containers
    shipments: DataFrame container_id, origin, planned_market, progress
    Types:
      RISK_DRIVEN       risk HIGH/CRITICAL, an alternative arrives sooner and its
                        quality-adjusted price beats the plan by >= MIN_ADVANTAGE_PCT
      PRICE_SPREAD_ONLY any alternative beats the plan by >= PRICE_ONLY_MIN_ADVANTAGE_PCT
                        (higher bar: freight/handling/market capacity are not modelled)
      NONE              neither
    """
    min_adv = C.MIN_ADVANTAGE_PCT if min_adv is None else min_adv
    price_only = C.PRICE_ONLY_MIN_ADVANTAGE_PCT if price_only_min_adv is None else price_only_min_adv
    merged = shipments.merge(risk_df[["container_id", "risk_score", "risk_level",
                                      "recent_decay_rate"]], on="container_id", how="inner")
    out = []
    for _, s in merged.iterrows():
        if s["planned_market"] not in price_by_market:
            continue
        pos = position_at(s["origin"], s["planned_market"], s["progress"])
        h_plan, net_plan, alts = evaluate_alternatives(
            pos, s["planned_market"], s["recent_decay_rate"], price_by_market, shelf_life_h)
        cand = alts[alts["extra_km"] <= C.MAX_EXTRA_KM]
        risky = s["risk_level"] in ("HIGH", "CRITICAL")
        base = {"container_id": s["container_id"], "origin": s["origin"],
                "planned_market": s["planned_market"], "progress": s["progress"],
                "risk_score": s["risk_score"], "risk_level": s["risk_level"],
                "planned_price": price_by_market[s["planned_market"]],
                "hours_to_planned": round(h_plan, 1), "net_planned": round(net_plan, 4)}
        best, kind = None, "NONE"
        if risky:
            rc = cand[cand["arrives_sooner"] & (cand["advantage_pct"] >= min_adv)]
            if not rc.empty:
                best, kind = rc.sort_values("advantage_pct", ascending=False).iloc[0], "RISK_DRIVEN"
        if best is None:
            pc = cand[cand["advantage_pct"] >= price_only]
            if not pc.empty:
                best, kind = pc.sort_values("advantage_pct", ascending=False).iloc[0], "PRICE_SPREAD_ONLY"
        if best is None:
            out.append({**base, "opportunity": kind, "alt_market": "", "advantage_pct": 0.0})
        else:
            out.append({**base, "opportunity": kind, "alt_market": best["alt_market"],
                        "alt_price": best["alt_price"], "extra_km": round(best["extra_km"], 0),
                        "hours_to_alt": round(best["hours_to_alt"], 1),
                        "net_alt": round(best["net_alt"], 4),
                        "advantage_pct": round(best["advantage_pct"], 2)})
    cols = ["container_id", "origin", "planned_market", "progress", "risk_score", "risk_level",
            "planned_price", "hours_to_planned", "net_planned", "opportunity", "alt_market",
            "alt_price", "extra_km", "hours_to_alt", "net_alt", "advantage_pct"]
    df = pd.DataFrame(out)
    for c in cols:
        if c not in df:
            df[c] = None
    order = {"RISK_DRIVEN": 0, "PRICE_SPREAD_ONLY": 1, "NONE": 2}
    df["_o"] = df["opportunity"].map(order)
    return df.sort_values(["_o", "advantage_pct"], ascending=[True, False]).drop(columns="_o")[cols].reset_index(drop=True)


def sensitivity(risk_df, shipments, price_by_market,
                shelf_lives=(504, 240, 120, 72), price_only_levels=(15, 25, 40)):
    """How many opportunities each assumption produces (transparency table)."""
    rows = []
    for life in shelf_lives:
        for po in price_only_levels:
            d = detect_opportunities(risk_df, shipments, price_by_market,
                                     shelf_life_h=life, price_only_min_adv=po)
            vc = d["opportunity"].value_counts()
            rows.append({"base_shelf_life_h": life, "price_only_min_adv_pct": po,
                         "risk_driven": int(vc.get("RISK_DRIVEN", 0)),
                         "price_spread_only": int(vc.get("PRICE_SPREAD_ONLY", 0)),
                         "none": int(vc.get("NONE", 0))})
    return pd.DataFrame(rows)
