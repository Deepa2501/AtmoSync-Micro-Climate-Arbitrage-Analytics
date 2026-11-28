import pandas as pd

from analytics.micro_climate.climate_analysis import (
    temperature_analysis,
    humidity_analysis,
    compare_locations
)


def sample_data():

    return pd.DataFrame({
        "location": [
            "Nashik", "Nashik",
            "Pune", "Pune"
        ],

        "temperature": [
            25, 30, 28, 32
        ],

        "humidity": [
            50, 60, 65, 70
        ],

        "precipitation": [
            0, 5, 2, 3
        ],

        "wind_speed": [
            10, 12, 8, 10
        ]
    })


def test_temperature_analysis():

    df = sample_data()

    result = temperature_analysis(df)

    assert len(result) == 2

    nashik = result[
        result["location"] == "Nashik"
    ]

    assert nashik["avg_temperature"].iloc[0] == 27.5


def test_humidity_analysis():

    df = sample_data()

    result = humidity_analysis(df)

    assert len(result) == 2


def test_location_comparison():

    df = sample_data()

    result = compare_locations(df)

    assert len(result) == 2

    assert "avg_temperature" in result.columns
    assert "avg_humidity" in result.columns