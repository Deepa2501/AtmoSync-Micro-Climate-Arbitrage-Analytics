import numpy as np
import pandas as pd

from analytics import config as C
from analytics import spoilage as S


def readings(cid, temps, hums):
    return pd.DataFrame({"container_id": cid, "temperature_c": temps, "humidity_pct": hums})


def test_decay_rate_reference_and_q10():
    assert S.decay_rate(C.T_REF_C) == 1.0
    assert np.isclose(S.decay_rate(C.T_REF_C + 10), C.Q10)


def test_weights_sum_to_100():
    assert C.W_TEMP_LEVEL + C.W_TEMP_DURATION + C.W_TEMP_TREND + C.W_HUMIDITY == 100


def test_inside_band_has_no_deviation():
    d = S.add_reading_indicators(readings("A", [5, 6, 7], [88, 90, 92]))
    assert (d["temp_dev_c"] == 0).all() and (d["hum_dev_pct"] == 0).all()


def test_healthy_container_scores_low():
    r = readings("OK", [6.0] * 24, [88.0] * 24)
    s = S.score_containers(r).iloc[0]
    assert s["risk_score"] == 0 and s["risk_level"] == "LOW"


def test_warming_container_scores_high():
    temps = [6 + 0.3 * i for i in range(24)]          # +0.3 C/h drift
    s = S.score_containers(readings("HOT", temps, [88.0] * 24)).iloc[0]
    assert s["risk_level"] in ("HIGH", "CRITICAL")
    assert s["temp_slope_c_per_h"] > 0.25


def test_score_is_ordered_and_bounded():
    both = pd.concat([readings("OK", [6.0] * 24, [88.0] * 24),
                      readings("HOT", [16.0] * 24, [99.0] * 24)])
    s = S.score_containers(both)
    assert list(s["container_id"]) == ["HOT", "OK"]
    assert ((s["risk_score"] >= 0) & (s["risk_score"] <= 100)).all()


def test_humidity_alone_cannot_exceed_its_weight():
    s = S.score_containers(readings("WET", [6.0] * 24, [99.9] * 24)).iloc[0]
    assert s["risk_score"] <= C.W_HUMIDITY
    assert s["risk_level"] in ("LOW", "MEDIUM")   # by design, humidity alone caps at MEDIUM


def test_short_series_slope_is_zero():
    assert S._slope_c_per_h([6.0, 7.0], 1.0) == 0.0
