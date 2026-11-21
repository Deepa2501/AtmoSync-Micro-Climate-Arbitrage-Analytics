
from streaming.simulators.iot_simulator import generate_sensor_reading


def test_sensor_reading_structure():
    reading = generate_sensor_reading()

    required_fields = [
        "sensor_id",
        "location",
        "temperature",
        "humidity",
        "vibration",
        "timestamp"
    ]

    for field in required_fields:
        assert field in reading


def test_sensor_reading_values():
    reading = generate_sensor_reading()

    assert reading["sensor_id"].startswith("SENSOR-")
    assert reading["location"] in [
        "New York",
        "Los Angeles",
        "Chicago"
    ]

    assert 15 <= reading["temperature"] <= 40
    assert 30 <= reading["humidity"] <= 90
    assert 0 <= reading["vibration"] <= 10


def test_sensor_reading_timestamp():
    reading = generate_sensor_reading()

    assert isinstance(reading["timestamp"], str)
    assert "T" in reading["timestamp"]