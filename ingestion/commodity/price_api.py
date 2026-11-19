
"""
Commodity price data ingestion module for AtmoSync.

Loads historical avocado prices, cleans the dataset,
validates essential fields, and saves processed data.
"""

import logging
from pathlib import Path

import pandas as pd


# Project directories
BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DATA_PATH = (
    BASE_DIR
    / "spoilage-arbitrage"
    / "data"
    / "avocado.csv"
)

PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"

PROCESSED_DATA_PATH = (
    PROCESSED_DATA_DIR / "avocado_prices_clean.csv"
)


logger = logging.getLogger(__name__)


# Required columns for price analysis
REQUIRED_COLUMNS = [
    "date",
    "average_price",
    "total_volume",
    "type",
    "year",
    "region",
]



def load_commodity_data(file_path=RAW_DATA_PATH):
    """
    Load historical avocado price data from CSV.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Commodity dataset not found: {file_path}"
        )

    logger.info("Loading commodity dataset: %s", file_path)

    df = pd.read_csv(file_path)

    # Remove unnecessary index column
    df = df.loc[
        :,
        ~df.columns.astype(str).str.startswith("Unnamed:")
    ]

    # Standardize column names
    df.columns = [
        str(column).strip().lower().replace(" ", "_")
        for column in df.columns
    ]

    # Fix original dataset column names
    df = df.rename(columns={
        "averageprice": "average_price",
        "totalvolume": "total_volume",
        "totalbags": "total_bags",
        "smallbags": "small_bags",
        "largebags": "large_bags",
        "xlargebags": "xlarge_bags",
    })

    logger.info("Loaded %s commodity records", len(df))

    logger.info("Dataset columns: %s", list(df.columns))

    return df


def clean_commodity_data(df):
    """
    Clean and standardize commodity price records.
    """

    df = df.copy()

    # Check required columns
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # Convert date column
    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    # Convert numeric columns
    numeric_columns = [
        "average_price",
        "total_volume",
        "year",
        "4046",
        "4225",
        "4770",
        "total_bags",
        "small_bags",
        "large_bags",
        "xlarge_bags",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # Remove records with missing essential values
    df = df.dropna(
        subset=REQUIRED_COLUMNS
    )

    # Remove invalid prices and volumes
    df = df[
        (df["average_price"] > 0)
        & (df["total_volume"] >= 0)
    ]

    # Standardize text columns
    df["type"] = df["type"].astype(str).str.strip().str.lower()
    df["region"] = df["region"].astype(str).str.strip()

    # Sort records chronologically
    df = df.sort_values(
        by=["date", "region"]
    ).reset_index(drop=True)

    logger.info(
        "Commodity cleaning completed. Valid records: %s",
        len(df)
    )

    return df


def save_commodity_data(df, output_path=PROCESSED_DATA_PATH):
    """
    Save cleaned commodity data to processed directory.
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        output_path,
        index=False
    )

    logger.info(
        "Processed commodity data saved to %s",
        output_path
    )


def run_commodity_ingestion():
    """
    Execute the complete commodity ingestion process.
    """

    raw_df = load_commodity_data()

    cleaned_df = clean_commodity_data(raw_df)

    save_commodity_data(cleaned_df)

    return cleaned_df


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    result = run_commodity_ingestion()

    print("\nCommodity ingestion completed!")
    print(f"Total records: {len(result)}")
    print(f"Date range: {result['date'].min()} to {result['date'].max()}")
    print(f"Regions: {result['region'].nunique()}")
    print(f"Output: {PROCESSED_DATA_PATH}")
