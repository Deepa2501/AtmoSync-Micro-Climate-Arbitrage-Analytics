import requests
import pandas as pd


from analytics.micro_climate.config import (
    LOCATIONS,
    START_DATE,
    END_DATE,
    TIMEZONE,
    WEATHER_API
)


def fetch_weather_data():

    all_data = []

    for city, coordinates in LOCATIONS.items():

        params = {
            "latitude": coordinates["latitude"],
            "longitude": coordinates["longitude"],
            "start_date": START_DATE,
            "end_date": END_DATE,
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation",
                "wind_speed_10m"
            ],
            "timezone": TIMEZONE
        }

        response = requests.get(
            WEATHER_API,
            params=params,
            timeout=60
        )

        response.raise_for_status()

        result = response.json()

        hourly = result["hourly"]

        df = pd.DataFrame({
            "timestamp": hourly["time"],
            "temperature": hourly["temperature_2m"],
            "humidity": hourly["relative_humidity_2m"],
            "precipitation": hourly["precipitation"],
            "wind_speed": hourly["wind_speed_10m"]
        })

        df["location"] = city

        all_data.append(df)

    weather_df = pd.concat(
        all_data,
        ignore_index=True
    )

    weather_df["timestamp"] = pd.to_datetime(
        weather_df["timestamp"]
    )

    return weather_df


def validate_weather_data(df):

    required_columns = [
        "timestamp",
        "location",
        "temperature",
        "humidity",
        "precipitation",
        "wind_speed"
    ]

    missing_columns = set(required_columns) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    print("\nLOCATION COVERAGE")

    print(
        df.groupby("location").agg(
            total_records=("timestamp", "count"),
            first_date=("timestamp", "min"),
            last_date=("timestamp", "max")
        )
    )

    print("\nMISSING VALUES")

    print(df[required_columns].isnull().sum())

    print("\nDUPLICATE RECORDS")

    print(
        df.duplicated(
            subset=["location", "timestamp"]
        ).sum()
    )

    print("\nUNIQUE LOCATIONS")

    print(df["location"].nunique())

    return df


if __name__ == "__main__":

    df = fetch_weather_data()

    df.to_csv(
        "data/raw/weather_data.csv",
        index=False
    )

    print(df.head())
    print("Total records:", len(df))

df = fetch_weather_data()

validate_weather_data(df)