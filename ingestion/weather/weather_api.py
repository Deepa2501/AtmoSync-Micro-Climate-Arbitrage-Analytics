
"""
Weather data ingestion module for AtmoSync.

Fetches weather observations and forecasts from Open-Meteo.
"""

import logging
from pathlib import Path

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
WEATHER_OUTPUT_PATH = PROCESSED_DATA_DIR / "weather_data.csv"

# Open-Meteo API endpoint
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

logger = logging.getLogger(__name__)


def fetch_weather_data(latitude, longitude, location_name):
    """
    Fetch current weather data for a location.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "wind_speed_10m"
        ),
        "timezone": "auto",
    }

    try:
        response = requests.get(
            WEATHER_API_URL,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        current = data.get("current")

        if not current:
            raise ValueError("Current weather data not found in API response")

        return {
            "location": location_name,
            "latitude": latitude,
            "longitude": longitude,
            "recorded_at": current.get("time"),
            "temperature_c": current.get("temperature_2m"),
            "humidity_percent": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
        }

    except requests.RequestException as error:
        logger.error(
            "Weather API request failed for %s: %s",
            location_name,
            error,
        )
        raise


def run_weather_ingestion():
    """
    Fetch weather data for configured sample locations.
    """

    locations = [
        {
            "name": "New York",
            "latitude": 40.7128,
            "longitude": -74.0060,
        },
        {
            "name": "Los Angeles",
            "latitude": 34.0522,
            "longitude": -118.2437,
        },
        {
            "name": "Chicago",
            "latitude": 41.8781,
            "longitude": -87.6298,
        },
    ]

    records = []

    for location in locations:
        logger.info(
            "Fetching weather for %s",
            location["name"],
        )

        record = fetch_weather_data(
            latitude=location["latitude"],
            longitude=location["longitude"],
            location_name=location["name"],
        )

        records.append(record)

    df = pd.DataFrame(records)

    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        WEATHER_OUTPUT_PATH,
        index=False,
    )

    logger.info(
        "Weather ingestion completed. Records: %s",
        len(df),
    )

    return df


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    result = run_weather_ingestion()

    print("\nWeather ingestion completed!")
    print(result.to_string(index=False))
    print(f"\nOutput saved to: {WEATHER_OUTPUT_PATH}")
