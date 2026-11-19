
"""
Data validation module for AtmoSync.

Validates processed commodity and weather datasets.
"""

import logging
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data" / "processed"

COMMODITY_FILE = DATA_DIR / "avocado_prices_clean.csv"
WEATHER_FILE = DATA_DIR / "weather_data.csv"

logger = logging.getLogger(__name__)


def validate_file_exists(file_path):
    """Check whether a dataset file exists."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )


def validate_commodity_data():
    """Validate processed commodity price data."""

    validate_file_exists(COMMODITY_FILE)

    df = pd.read_csv(COMMODITY_FILE)

    required_columns = [
        "date",
        "average_price",
        "total_volume",
        "type",
        "year",
        "region",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Commodity dataset missing columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError("Commodity dataset is empty")

    if df[required_columns].isnull().any().any():
        raise ValueError(
            "Commodity dataset contains missing required values"
        )

    if (df["average_price"] <= 0).any():
        raise ValueError("Invalid commodity prices found")

    if (df["total_volume"] < 0).any():
        raise ValueError("Invalid commodity volume found")

    logger.info(
        "Commodity validation successful: %s records",
        len(df),
    )

    return True


def validate_weather_data():
    """Validate processed weather data."""

    validate_file_exists(WEATHER_FILE)

    df = pd.read_csv(WEATHER_FILE)

    required_columns = [
        "location",
        "latitude",
        "longitude",
        "recorded_at",
        "temperature_c",
        "humidity_percent",
        "precipitation_mm",
        "wind_speed_kmh",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Weather dataset missing columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError("Weather dataset is empty")

    if df[required_columns].isnull().any().any():
        raise ValueError(
            "Weather dataset contains missing required values"
        )

    if not df["humidity_percent"].between(0, 100).all():
        raise ValueError("Invalid humidity values found")

    if (df["precipitation_mm"] < 0).any():
        raise ValueError("Invalid precipitation values found")

    if (df["wind_speed_kmh"] < 0).any():
        raise ValueError("Invalid wind speed values found")

    logger.info(
        "Weather validation successful: %s records",
        len(df),
    )

    return True


def run_all_validations():
    """Run validation on all processed datasets."""

    logger.info("Starting AtmoSync data validation")

    commodity_status = validate_commodity_data()
    weather_status = validate_weather_data()

    if commodity_status and weather_status:
        logger.info("All dataset validations passed!")
        print("\nAll AtmoSync data validations passed!")

    return True


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    run_all_validations()
