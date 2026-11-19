
"""
Main ingestion pipeline for AtmoSync.

Runs commodity ingestion, weather ingestion,
and data validation in sequence.
"""

import logging

from ingestion.commodity.price_api import run_commodity_ingestion
from ingestion.weather.weather_api import run_weather_ingestion
from ingestion.data_validator import run_all_validations

logger = logging.getLogger(__name__)


def run_pipeline():
    """Execute the complete AtmoSync ingestion pipeline."""

    logger.info("Starting AtmoSync ingestion pipeline")

    try:
        # Step 1: Commodity ingestion
        logger.info("Step 1: Commodity data ingestion")
        commodity_df = run_commodity_ingestion()

        # Step 2: Weather ingestion
        logger.info("Step 2: Weather data ingestion")
        weather_df = run_weather_ingestion()

        # Step 3: Data validation
        logger.info("Step 3: Data validation")
        run_all_validations()

        logger.info("AtmoSync ingestion pipeline completed successfully!")

        print("\n========== PIPELINE SUMMARY ==========")
        print(f"Commodity records: {len(commodity_df)}")
        print(f"Weather records: {len(weather_df)}")
        print("Data validation: PASSED")
        print("Pipeline status: SUCCESS")
        print("======================================")

        return True

    except Exception:
        logger.exception("AtmoSync ingestion pipeline failed")
        raise


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    run_pipeline()
