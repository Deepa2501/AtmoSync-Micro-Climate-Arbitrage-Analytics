
import pandas as pd
import pytest

from ingestion.commodity.price_api import clean_commodity_data


def test_clean_commodity_data_keeps_valid_records():
    sample_data = pd.DataFrame({
        "date": ["2015-12-27", "2015-12-28"],
        "average_price": [1.25, -2.0],
        "total_volume": [1000, 2000],
        "type": ["conventional", "organic"],
        "year": [2015, 2015],
        "region": ["Albany", "Boston"],
    })

    result = clean_commodity_data(sample_data)

    assert len(result) == 1
    assert result.iloc[0]["average_price"] == 1.25
    assert result.iloc[0]["region"] == "Albany"


def test_clean_commodity_data_rejects_missing_columns():
    sample_data = pd.DataFrame({
        "date": ["2015-12-27"],
        "average_price": [1.25],
    })

    with pytest.raises(ValueError, match="Missing required columns"):
        clean_commodity_data(sample_data)


def test_clean_commodity_data_returns_sorted_dates():
    sample_data = pd.DataFrame({
        "date": ["2015-12-28", "2015-12-27"],
        "average_price": [1.50, 1.25],
        "total_volume": [2000, 1000],
        "type": ["organic", "conventional"],
        "year": [2015, 2015],
        "region": ["Boston", "Albany"],
    })

    result = clean_commodity_data(sample_data)

    assert result["date"].is_monotonic_increasing
