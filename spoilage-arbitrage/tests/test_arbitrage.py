from pathlib import Path

import pandas as pd
import pytest

from analytics import arbitrage as A
from analytics import config as C
from analytics import spoilage as S

ROOT = Path(__file__).resolve().parent.parent
PRICES = ROOT / "data" / "avocado.csv"
SAMPLES = ROOT / "outputs"


def risk_row(cid, level, rate=1.0, score=0.0):
    return pd.DataFrame([{"container_id": cid, "risk_score": score,
                          "risk_level": level, "recent_decay_rate": rate}])


def ship(cid="X", origin="Pharr", planned="Houston", progress=0.3):
    return pd.DataFrame([{"container_id": cid, "origin": origin,
                          "planned_market": planned, "progress": progress}])


def flat_prices(**overrides):
    p = {name: 1.0 for name, *_ in C.MARKETS_REF}
    p.update(overrides)
    return p


def test_haversine_la_to_ny():
    d = A.haversine_km(A.MARKET_COORDS["Los Angeles"], A.MARKET_COORDS["New York"])
    assert 3900 < d < 4000


def test_position_at_ends():
    o = C.ORIGINS_REF["Pharr"]
    assert A.position_at("Pharr", "Houston", 0) == o
    assert A.position_at("Pharr", "Houston", 1) == A.MARKET_COORDS["Houston"]


def test_expected_loss_bounds():
    assert A.expected_loss_fraction(1.0, 0) == 0
    assert A.expected_loss_fraction(5.0, 10_000) == 1.0


def test_equal_prices_no_opportunity():
    d = A.detect_opportunities(risk_row("X", "LOW"), ship(), flat_prices())
    assert d.loc[0, "opportunity"] == "NONE"


def test_large_price_gap_is_price_spread_only():
    d = A.detect_opportunities(risk_row("X", "LOW"), ship(planned="Houston"),
                               flat_prices(Dallas=2.0))
    assert d.loc[0, "opportunity"] == "PRICE_SPREAD_ONLY"
    assert d.loc[0, "alt_market"] == "Dallas"


def test_small_price_gap_below_price_only_bar_is_none():
    d = A.detect_opportunities(risk_row("X", "LOW"), ship(planned="Houston"),
                               flat_prices(Dallas=1.10))
    assert d.loc[0, "opportunity"] == "NONE"


def test_risk_driven_needs_high_risk_and_sooner_arrival():
    # Short shelf life makes arrival time matter; Dallas pays more and is nearer than Boston plan.
    p = flat_prices(Dallas=1.2)
    kw = dict(shelf_life_h=48)
    high = A.detect_opportunities(risk_row("X", "HIGH", rate=3.0),
                                  ship(origin="Pharr", planned="Boston", progress=0.2), p, **kw)
    low = A.detect_opportunities(risk_row("X", "LOW", rate=3.0),
                                 ship(origin="Pharr", planned="Boston", progress=0.2), p, **kw)
    assert high.loc[0, "opportunity"] == "RISK_DRIVEN"
    assert low.loc[0, "opportunity"] != "RISK_DRIVEN"


def test_detour_beyond_limit_is_excluded():
    # Seattle is far from Miami-bound cargo: even at a huge price it exceeds MAX_EXTRA_KM
    d = A.detect_opportunities(risk_row("X", "LOW"),
                               ship(origin="Pharr", planned="Miami", progress=0.3),
                               {**flat_prices(), "Seattle": 50.0, "Miami": 1.0})
    if d.loc[0, "opportunity"] != "NONE":
        assert d.loc[0, "extra_km"] <= C.MAX_EXTRA_KM


def test_load_prices_keeps_only_reference_markets():
    p = A.load_prices(PRICES)
    assert set(p["market"]) == {m[0] for m in C.MARKETS_REF}


def test_regional_summary_columns_and_gaps():
    p = A.load_prices(PRICES)
    s = A.regional_price_summary(p)
    assert {"market", "mean_price", "vs_market_mean_pct"} <= set(s.columns)
    gaps = A.price_gap_pairs(A.current_prices(p))
    assert (gaps["gap"] >= 0).all() and gaps["gap"].is_monotonic_decreasing


@pytest.mark.skipif(not (SAMPLES / "sample_readings.jsonl").exists(), reason="sample data missing")
def test_sample_run_flags_injected_temperature_drifts():
    """Seed-42 simulator sample: CNT-0001 and CNT-0002 have injected temp_drift."""
    r = pd.read_json(SAMPLES / "sample_readings.jsonl", lines=True)
    s = S.score_containers(r).set_index("container_id")
    assert s.loc["CNT-0001", "risk_level"] in ("HIGH", "CRITICAL")
    assert s.loc["CNT-0002", "risk_level"] in ("HIGH", "CRITICAL")
    assert (s.drop(["CNT-0001", "CNT-0002"])["risk_level"] != "CRITICAL").all()
