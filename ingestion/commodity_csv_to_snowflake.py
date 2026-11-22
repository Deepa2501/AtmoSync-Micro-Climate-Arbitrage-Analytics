
import csv
from pathlib import Path

from snowflake_service.connection import get_snowflake_connection


ROOT = Path(__file__).resolve().parents[1]
CSV_FILE = ROOT / "data" / "sample" / "commodity_prices.csv"


INSERT_QUERY = """
MERGE INTO ATMOSYNC_DB.RAW.RAW_COMMODITY_PRICES target
USING (
    SELECT
        %s AS COMMODITY,
        %s AS MARKET,
        %s AS STATE,
        %s AS PRICE_PER_QUINTAL,
        %s AS MIN_PRICE,
        %s AS MAX_PRICE,
        TO_DATE(%s) AS PRICE_DATE
) source

ON target.COMMODITY = source.COMMODITY
AND target.MARKET = source.MARKET
AND target.STATE = source.STATE
AND target.PRICE_DATE = source.PRICE_DATE

WHEN MATCHED THEN UPDATE SET
    PRICE_PER_QUINTAL = source.PRICE_PER_QUINTAL,
    MIN_PRICE = source.MIN_PRICE,
    MAX_PRICE = source.MAX_PRICE

WHEN NOT MATCHED THEN INSERT (
    COMMODITY,
    MARKET,
    STATE,
    PRICE_PER_QUINTAL,
    MIN_PRICE,
    MAX_PRICE,
    PRICE_DATE
)
VALUES (
    source.COMMODITY,
    source.MARKET,
    source.STATE,
    source.PRICE_PER_QUINTAL,
    source.MIN_PRICE,
    source.MAX_PRICE,
    source.PRICE_DATE
)
"""


# Map different CSV header names to standard names
COLUMN_ALIASES = {
    "COMMODITY": ["COMMODITY", "CROP", "COMMODITY_NAME"],
    "MARKET": ["MARKET", "MANDI", "MARKET_NAME"],
    "STATE": ["STATE", "STATE_NAME"],
    "PRICE_PER_QUINTAL": [
        "PRICE_PER_QUINTAL",
        "MODAL_PRICE",
        "MODALPRICE",
        "PRICE"
    ],
    "MIN_PRICE": ["MIN_PRICE", "MINIMUM_PRICE"],
    "MAX_PRICE": ["MAX_PRICE", "MAXIMUM_PRICE"],
    "PRICE_DATE": [
        "PRICE_DATE",
        "ARRIVAL_DATE",
        "DATE"
    ]
}


def normalize_header(header):
    return header.strip().replace("\ufeff", "").upper().replace(" ", "_")


def load_commodity_data():

    if not CSV_FILE.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_FILE}")

    conn = None
    cursor = None

    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        print("Snowflake connected successfully!")

        with open(CSV_FILE, "r", newline="", encoding="utf-8-sig") as file:

            reader = csv.DictReader(file)

            if not reader.fieldnames:
                raise ValueError("CSV file has no column headers.")

            # Normalize CSV headers
            original_headers = reader.fieldnames
            normalized_headers = {
                normalize_header(header): header
                for header in original_headers
            }

            print("CSV columns:", list(normalized_headers.keys()))

            # Find matching columns
            column_mapping = {}

            for standard_name, aliases in COLUMN_ALIASES.items():

                matched = next(
                    (
                        alias
                        for alias in aliases
                        if alias in normalized_headers
                    ),
                    None
                )

                if matched:
                    column_mapping[standard_name] = normalized_headers[matched]

            # Check missing columns
            required_columns = list(COLUMN_ALIASES.keys())

            missing = [
                col for col in required_columns
                if col not in column_mapping
            ]

            if missing:
                raise ValueError(
                    f"Missing CSV columns: {missing}. "
                    f"Available columns: {list(normalized_headers.keys())}"
                )

            inserted = 0

            for row in reader:

                def get_value(column):
                    value = row[column_mapping[column]]
                    return value.strip() if value else None

                def get_number(column):
                    value = get_value(column)
                    if value is None or value == "":
                        return None
                    return float(value.replace(",", ""))

                values = (
                    get_value("COMMODITY"),
                    get_value("MARKET"),
                    get_value("STATE"),
                    get_number("PRICE_PER_QUINTAL"),
                    get_number("MIN_PRICE"),
                    get_number("MAX_PRICE"),
                    get_value("PRICE_DATE")
                )

                if not values[0]:
                    continue

                cursor.execute(INSERT_QUERY, values)
                inserted += 1

            conn.commit()

            print("--------------------------------")
            print("Commodity CSV ingestion completed!")
            print("Records processed:", inserted)
            print("--------------------------------")

    except Exception as error:

        if conn:
            conn.rollback()

        print("CSV ingestion failed:", error)
        raise

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


if __name__ == "__main__":
    load_commodity_data()
