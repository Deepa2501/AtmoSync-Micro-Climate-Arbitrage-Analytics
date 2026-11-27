from dataclasses import _DataclassFactory


def calculate_climate_indicators(df):

    indicators = df.groupby("location").agg(

        avg_temperature=("temperature", "mean"),

        temperature_range=(
            "temperature",
            lambda x: x.max() - x.min()
        ),

        temperature_variability=(
            "temperature",
            "std"
        ),

        avg_humidity=("humidity", "mean"),

        total_rainfall=("precipitation", "sum"),

        avg_wind_speed=("wind_speed", "mean")

    ).reset_index()

    return indicators

indicators = calculate_climate_indicators(_DataclassFactory)

indicators.to_csv(
    "data/processed/climate_indicators.csv",
    index=False
)