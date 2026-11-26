"""All assumptions for spoilage scoring and arbitrage detection live here.

IMPORTANT: every value below is an ASSUMPTION chosen for a development
prototype. None of them has been calibrated or verified against real
shipment or postharvest data. Change them here, not in the logic.
"""

# ---- Avocado storage assumptions (spoilage.py) -------------------------------
TEMP_BAND_C = (4.0, 8.0)          # acceptable reefer temperature band
HUMIDITY_BAND_PCT = (85.0, 95.0)  # acceptable relative humidity band
Q10 = 2.0                         # decay-rate multiplier per +10 C (generic assumption)
T_REF_C = 6.0                     # temperature where relative decay rate = 1.0
BASE_SHELF_LIFE_H = 504.0         # shelf life at T_REF_C (21 days), assumption
STEP_HOURS = 1.0                  # time between readings (see note in docs)
RECENT_N = 6                      # readings used for "current condition"

# ---- Risk score: max points per component (sum = 100) ------------------------
W_TEMP_LEVEL = 50                 # recent temperature outside band
W_TEMP_DURATION = 15              # share of readings outside band
W_TEMP_TREND = 10                 # warming trend (drift)
W_HUMIDITY = 25                   # recent humidity outside band
TEMP_DEV_SATURATION_C = 6.0       # deviation giving full temp-level points
SLOPE_MIN_C_PER_H = 0.05          # trend below this scores 0
SLOPE_MAX_C_PER_H = 0.30          # trend at/above this scores full points
HUM_DEV_SATURATION_PCT = 3.0      # deviation giving full humidity points

RISK_LEVELS = [(75, "CRITICAL"), (50, "HIGH"), (25, "MEDIUM"), (0, "LOW")]

# ---- Arbitrage assumptions (arbitrage.py) ------------------------------------
TRANSPORT_SPEED_KMH = 70.0        # road speed, straight-line distance only
MIN_ADVANTAGE_PCT = 5.0           # min quality-adjusted price gain to flag
PRICE_ONLY_MIN_ADVANTAGE_PCT = 25.0  # higher bar when risk is not the reason
MAX_EXTRA_KM = 1500.0             # max extra distance vs planned market
DETOUR_PENALTY_PCT_PER_1000KM = 1.0  # crude cost proxy for extra distance
PRICE_WINDOW_WEEKS = 4            # weeks averaged for a market's price

# Must match MARKETS in scripts/load_reference_data.py: (name, region_key, lat, lon)
MARKETS_REF = [
    ("Los Angeles", "LosAngeles", 34.0522, -118.2437),
    ("San Diego", "SanDiego", 32.7157, -117.1611),
    ("San Francisco", "SanFrancisco", 37.7749, -122.4194),
    ("Seattle", "Seattle", 47.6062, -122.3321),
    ("Phoenix", "PhoenixTucson", 33.4484, -112.0740),
    ("Las Vegas", "LasVegas", 36.1699, -115.1398),
    ("Denver", "Denver", 39.7392, -104.9903),
    ("Houston", "Houston", 29.7604, -95.3698),
    ("Dallas", "DallasFtWorth", 32.7767, -96.7970),
    ("Chicago", "Chicago", 41.8781, -87.6298),
    ("Detroit", "Detroit", 42.3314, -83.0458),
    ("Atlanta", "Atlanta", 33.7490, -84.3880),
    ("Miami", "MiamiFtLauderdale", 25.7617, -80.1918),
    ("Philadelphia", "Philadelphia", 39.9526, -75.1652),
    ("New York", "NewYork", 40.7128, -74.0060),
    ("Boston", "Boston", 42.3601, -71.0589),
]
# Must match ORIGINS in scripts/load_reference_data.py: name -> (lat, lon)
ORIGINS_REF = {
    "Uruapan": (19.4167, -102.0667),
    "Lazaro Cardenas": (17.9583, -102.2000),
    "Pharr": (26.1948, -98.1836),
}
