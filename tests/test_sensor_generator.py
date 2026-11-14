
from ingestion.sensor_generator import (
    generate_sensor_data,
    CONTAINERS
)


def test_sensor_data_structure():

    data = generate_sensor_data("CONT001")

    assert "event_id" in data
    assert "container_id" in data
    assert "location" in data
    assert "commodity" in data
    assert "temperature" in data
    assert "humidity" in data
    assert "vibration" in data
    assert "timestamp" in data


def test_sensor_values():

    data = generate_sensor_data("CONT001")

    assert 5 <= data["temperature"] <= 40
    assert 30 <= data["humidity"] <= 95
    assert 0.1 <= data["vibration"] <= 5.0


def test_container_details():

    data = generate_sensor_data("CONT002")

    assert data["commodity"] == "Onion"
    assert data["location"] == "Pune"
