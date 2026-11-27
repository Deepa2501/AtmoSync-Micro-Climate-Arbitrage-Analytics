import plotly.express as px


def plot_temperature_comparison(df):

    summary = df.groupby("location")[
        "temperature"
    ].mean().reset_index()

    fig = px.bar(
        summary,
        x="location",
        y="temperature",
        title="Average Temperature by Location",
        labels={
            "location": "Location",
            "temperature": "Temperature (°C)"
        }
    )

    fig.write_html(
        "reports/micro_climate/temperature.html"
    )

    fig.show()