
"""
Central configuration settings for AtmoSync.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from the project root
load_dotenv(BASE_DIR / ".env")


# Application settings
APP_NAME = os.getenv("APP_NAME", "AtmoSync")
APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


# Kafka settings
KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092"
)

KAFKA_SENSOR_TOPIC = os.getenv(
    "KAFKA_SENSOR_TOPIC",
    "iot.sensor.readings"
)


# Snowflake settings
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT", "")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER", "")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD", "")

SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "RAW")
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE", "")

SNOWFLAKE_PRIVATE_KEY_PATH = os.getenv(
    "SNOWFLAKE_PRIVATE_KEY_PATH",
    ""
)


def get_snowflake_config():
    """
    Return Snowflake configuration.

    Raises an error if essential connection details are missing.
    """

    required_settings = {
        "SNOWFLAKE_ACCOUNT": SNOWFLAKE_ACCOUNT,
        "SNOWFLAKE_USER": SNOWFLAKE_USER,
        "SNOWFLAKE_WAREHOUSE": SNOWFLAKE_WAREHOUSE,
        "SNOWFLAKE_DATABASE": SNOWFLAKE_DATABASE,
    }

    missing_settings = [
        key for key, value in required_settings.items() if not value
    ]

    if missing_settings:
        raise ValueError(
            "Missing Snowflake settings: "
            + ", ".join(missing_settings)
        )

    return {
        "account": SNOWFLAKE_ACCOUNT,
        "user": SNOWFLAKE_USER,
        "warehouse": SNOWFLAKE_WAREHOUSE,
        "database": SNOWFLAKE_DATABASE,
        "schema": SNOWFLAKE_SCHEMA,
        "role": SNOWFLAKE_ROLE,
        "password": SNOWFLAKE_PASSWORD,
        "private_key_path": SNOWFLAKE_PRIVATE_KEY_PATH,
    }
