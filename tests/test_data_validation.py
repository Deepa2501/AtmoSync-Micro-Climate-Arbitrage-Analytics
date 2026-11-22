def test_commodity_csv_exists():
    from pathlib import Path

    file_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "sample"
        / "commodity_prices.csv"
    )

    assert file_path.exists()


def test_sensor_generator():
    from ingestion.sensor_generator import generate_sensor_data

    data = generate_sensor_data("CONT001")

    assert data["event_id"]
    assert data["temperature"] is not None
    assert data["humidity"] is not None