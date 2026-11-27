def temperature_analysis(df):

    result = df.groupby("location").agg(
        avg_temperature=("temperature", "mean"),
        max_temperature=("temperature", "max"),
        min_temperature=("temperature", "min"),
        temperature_std=("temperature", "std")
    ).reset_index()

    return result
def humidity_analysis(df):

    result = df.groupby("location").agg(
        avg_humidity=("humidity", "mean"),
        max_humidity=("humidity", "max"),
        min_humidity=("humidity", "min")
    ).reset_index()

    return result
def precipitation_analysis(df):

    result = df.groupby("location").agg(
        total_precipitation=("precipitation", "sum"),
        avg_precipitation=("precipitation", "mean"),
        max_precipitation=("precipitation", "max")
    ).reset_index()

    return result
def wind_analysis(df):

    result = df.groupby("location").agg(
        avg_wind_speed=("wind_speed", "mean"),
        max_wind_speed=("wind_speed", "max")
    ).reset_index()

    return result
def compare_locations(df):

    result = df.groupby("location").agg(
        avg_temperature=("temperature", "mean"),
        avg_humidity=("humidity", "mean"),
        total_precipitation=("precipitation", "sum"),
        avg_wind_speed=("wind_speed", "mean")
    ).reset_index()

    return result
def climate_correlation(df):

    columns = [
        "temperature",
        "humidity",
        "precipitation",
        "wind_speed"
    ]

    correlation = df[columns].corr(
        method="pearson"
    )

    return correlation