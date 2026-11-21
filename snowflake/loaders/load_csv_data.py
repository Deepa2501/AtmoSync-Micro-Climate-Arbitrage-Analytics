
import csv
from pathlib import Path

from config.snowflake_connection import get_snowflake_connection

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def load_commodity_data(cursor):
    file_path = PROCESSED_DIR / "avocado_prices_clean.csv"

    query = """
        INSERT INTO ATMOSYNC_DB.RAW.RAW_COMMODITY_PRICES (
            DATE, AVERAGE_PRICE, TOTAL_VOLUME,
            PLU_4046, PLU_4225, PLU_4770,
            TOTAL_BAGS, SMALL_BAGS, LARGE_BAGS,
            XLARGE_BAGS, TYPE, YEAR, REGION
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
    """

    with open(file_path, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = [
            (
                row["date"], row["average_price"], row["total_volume"],
                row["4046"], row["4225"], row["4770"],
                row["total_bags"], row["small_bags"],
                row["large_bags"], row["xlarge_bags"],
                row["type"], row["year"], row["region"]
            )
            for row in reader
        ]

    cursor.executemany(query, rows)
    print(f"Commodity records loaded: {len(rows)}")


def load_weather_data(cursor):
    file_path = PROCESSED_DIR / "weather_data.csv"

    query = """
        INSERT INTO ATMOSYNC_DB.RAW.RAW_WEATHER_DATA (
            LOCATION, LATITUDE, LONGITUDE, RECORDED_AT,
            TEMPERATURE_C, HUMIDITY_PERCENT,
            PRECIPITATION_MM, WIND_SPEED_KMH
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    with open(file_path, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = [
            (
                row["location"], row["latitude"], row["longitude"],
                row["recorded_at"], row["temperature_c"],
                row["humidity_percent"], row["precipitation_mm"],
                row["wind_speed_kmh"]
            )
            for row in reader
        ]

    cursor.executemany(query, rows)
    print(f"Weather records loaded: {len(rows)}")


def main():
    connection = get_snowflake_connection()

    try:
        cursor = connection.cursor()

        try:
            load_commodity_data(cursor)
            load_weather_data(cursor)

            connection.commit()
            print("All CSV data loaded successfully!")

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()

    finally:
        connection.close()


if __name__ == "__main__":
    main()
