"""Spoilage indicators and rule-based risk score from temperature/humidity.

Input: DataFrame with columns container_id, temperature_c, humidity_pct,
rows in time order per container (the simulator's event_ts is wall-clock,
so readings are treated as evenly spaced by config.STEP_HOURS).
Output scores are RELATIVE RISK INDICATORS, not predicted spoilage.
"""
import numpy as np
import pandas as pd

from . import config as C


def decay_rate(temp_c):
    """Relative decay-rate multiplier (Q10 model): 1.0 at T_REF_C."""
    return np.power(C.Q10, (np.asarray(temp_c, dtype=float) - C.T_REF_C) / 10.0)


def _band_deviation(values, band):
    """Distance outside [low, high]; 0 when inside the band."""
    lo, hi = band
    v = np.asarray(values, dtype=float)
    return np.maximum(0.0, np.maximum(v - hi, lo - v))


def add_reading_indicators(df):
    """Per-reading indicators (adds columns, returns a copy)."""
    out = df.copy()
    out["temp_dev_c"] = _band_deviation(out["temperature_c"], C.TEMP_BAND_C)
    out["hum_dev_pct"] = _band_deviation(out["humidity_pct"], C.HUMIDITY_BAND_PCT)
    out["decay_rate"] = decay_rate(out["temperature_c"])
    out["temp_out_of_band"] = out["temp_dev_c"] > 0
    out["hum_out_of_band"] = out["hum_dev_pct"] > 0
    return out


def _slope_c_per_h(temps, step_hours):
    if len(temps) < 3:
        return 0.0
    x = np.arange(len(temps)) * step_hours
    return float(np.polyfit(x, np.asarray(temps, dtype=float), 1)[0])


def container_indicators(df, step_hours=None):
    """One row per container with aggregate indicators."""
    step = C.STEP_HOURS if step_hours is None else step_hours
    d = add_reading_indicators(df)
    rows = []
    for cid, g in d.groupby("container_id", sort=True):
        recent = g.tail(C.RECENT_N)
        rows.append({
            "container_id": cid,
            "n_readings": len(g),
            "mean_temp_c": g["temperature_c"].mean(),
            "max_temp_c": g["temperature_c"].max(),
            "recent_temp_c": recent["temperature_c"].mean(),
            "mean_humidity_pct": g["humidity_pct"].mean(),
            "recent_humidity_pct": recent["humidity_pct"].mean(),
            "recent_temp_dev_c": recent["temp_dev_c"].mean(),
            "recent_hum_dev_pct": recent["hum_dev_pct"].mean(),
            "share_temp_out_of_band": g["temp_out_of_band"].mean(),
            "share_hum_out_of_band": g["hum_out_of_band"].mean(),
            "temp_slope_c_per_h": _slope_c_per_h(g["temperature_c"], step),
            "recent_decay_rate": recent["decay_rate"].mean(),
            "degree_hours_above_band": float((g["temperature_c"] - C.TEMP_BAND_C[1]).clip(lower=0).sum() * step),
        })
    return pd.DataFrame(rows)


def risk_level(score):
    for threshold, name in C.RISK_LEVELS:
        if score >= threshold:
            return name
    return "LOW"


def score_row(r):
    """Rule-based score (0-100) with its component points."""
    temp_level = C.W_TEMP_LEVEL * min(1.0, r["recent_temp_dev_c"] / C.TEMP_DEV_SATURATION_C)
    duration = C.W_TEMP_DURATION * r["share_temp_out_of_band"]
    span = C.SLOPE_MAX_C_PER_H - C.SLOPE_MIN_C_PER_H
    trend = C.W_TEMP_TREND * min(1.0, max(0.0, (r["temp_slope_c_per_h"] - C.SLOPE_MIN_C_PER_H) / span))
    humidity = C.W_HUMIDITY * min(1.0, r["recent_hum_dev_pct"] / C.HUM_DEV_SATURATION_PCT)
    total = temp_level + duration + trend + humidity
    return {"pts_temp_level": temp_level, "pts_temp_duration": duration,
            "pts_temp_trend": trend, "pts_humidity": humidity,
            "risk_score": round(total, 1), "risk_level": risk_level(total)}


def score_containers(readings, step_hours=None):
    ind = container_indicators(readings, step_hours)
    scores = pd.DataFrame([score_row(r) for _, r in ind.iterrows()])
    out = pd.concat([ind, scores], axis=1)
    return out.sort_values("risk_score", ascending=False).reset_index(drop=True)
