"""Load real avocado prices (Kaggle / Hass Avocado Board) plus market and
origin reference tables into Snowflake RAW schema.

Run from the spoilage-arbitrage/ folder:
    python scripts/load_reference_data.py
"""
from pathlib import Path

import pandas as pd
import snowflake.connector
from cryptography.hazmat.primitives import serialization
from snowflake.connector.pandas_tools import write_pandas

ROOT = Path(__file__).resolve().parent.parent
ACCOUNT = "ZPLZZLB-NK45236"

# region_key must match the 'region' column in avocado.csv exactly
MARKETS = [
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

# Origin hubs: packing / export points for Mexican avocados
ORIGINS = [
    ("Uruapan", "MX", 19.4167, -102.0667),
    ("Lazaro Cardenas", "MX", 17.9583, -102.2000),
    ("Pharr", "US", 26.1948, -98.1836),
]


def build_frames():
    prices = pd.read_csv(ROOT / "data" / "avocado.csv")
    prices = prices.drop(columns=["Unnamed: 0"])
    prices.columns = [
        "PRICE_DATE", "AVERAGE_PRICE", "TOTAL_VOLUME", "PLU_4046", "PLU_4225",
        "PLU_4770", "TOTAL_BAGS", "SMALL_BAGS", "LARGE_BAGS", "XLARGE_BAGS",
        "AVOCADO_TYPE", "YEAR", "REGION",
    ]
    prices["PRICE_DATE"] = pd.to_datetime(prices["PRICE_DATE"]).dt.strftime("%Y-%m-%d")

    markets = pd.DataFrame(
        MARKETS, columns=["MARKET_NAME", "REGION_KEY", "LAT", "LON"]
    )
    markets["COUNTRY"] = "US"
    origins = pd.DataFrame(ORIGINS, columns=["ORIGIN_NAME", "COUNTRY", "LAT", "LON"])
    return prices, markets, origins


def connect():
    with open(ROOT / "snowflake_key.p8", "rb") as f:
        key = serialization.load_pem_private_key(f.read(), password=None)
    der = key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return snowflake.connector.connect(
        account=ACCOUNT,
        user="PIPELINE_USER",
        private_key=der,
        warehouse="SPOILAGE_WH",
        database="SPOILAGE_DB",
        schema="RAW",
    )


def main():
    prices, markets, origins = build_frames()
    conn = connect()
    try:
        for name, df in [
            ("AVOCADO_PRICES", prices),
            ("MARKETS", markets),
            ("ORIGINS", origins),
        ]:
            ok, _, nrows, _ = write_pandas(
                conn, df, name, auto_create_table=True, overwrite=True
            )
            print(f"RAW.{name}: loaded={ok} rows={nrows}")
        cur = conn.cursor()
        cur.execute("SELECT MIN(PRICE_DATE), MAX(PRICE_DATE) FROM RAW.AVOCADO_PRICES")
        print("price date range:", cur.fetchone())
    finally:
        conn.close()


if __name__ == "__main__":
    main()
