
import pytest
from datetime import datetime, timezone

from streaming.consumers.snowflake_sink_consumer import (
    validate_sensor_reading,
    insert_sensor_reading,
    INSERT_SENSOR_SQL
)


@pytest.fixture
def valid_sensor_data():
    return {
        "sensor_id": "SENSOR-001",
        "location": "New York",
        "temperature": 25.5,
        "humidity": 60.0,
        "vibration": 3.2,
        "timestamp": "2026-11-22T01:00:00+00:00"
    }


def test_valid_sensor_reading(valid_sensor_data):
    result = validate_sensor_reading(valid_sensor_data)

    assert result[0] == "SENSOR-001"
    assert result[1] == "New York"
    assert result[2] == 25.5
    assert result[3] == 60.0
    assert result[4] == 3.2
    assert result[5].tzinfo is not None


def test_missing_sensor_field(valid_sensor_data):
    del valid_sensor_data["temperature"]

    with pytest.raises(ValueError, match="Missing fields"):
        validate_sensor_reading(valid_sensor_data)


def test_invalid_numeric_value(valid_sensor_data):
    valid_sensor_data["temperature"] = "hot"

    with pytest.raises(ValueError, match="Invalid numeric field"):
        validate_sensor_reading(valid_sensor_data)


def test_boolean_numeric_value_rejected(valid_sensor_data):
    valid_sensor_data["humidity"] = True

    with pytest.raises(ValueError, match="Invalid numeric field"):
        validate_sensor_reading(valid_sensor_data)


def test_non_finite_numeric_value_rejected(valid_sensor_data):
    valid_sensor_data["temperature"] = float("nan")

    with pytest.raises(ValueError, match="Non-finite value"):
        validate_sensor_reading(valid_sensor_data)


def test_invalid_timestamp(valid_sensor_data):
    valid_sensor_data["timestamp"] = "not-a-timestamp"

    with pytest.raises(ValueError, match="Invalid sensor timestamp"):
        validate_sensor_reading(valid_sensor_data)


def test_timezone_required(valid_sensor_data):
    valid_sensor_data["timestamp"] = "2026-11-22T01:00:00"

    with pytest.raises(ValueError, match="timezone"):
        validate_sensor_reading(valid_sensor_data)


def test_non_dictionary_message_rejected():
    with pytest.raises(ValueError, match="JSON object"):
        validate_sensor_reading([])


def test_snowflake_insert_uses_parameterized_query():
    class MockCursor:
        def __init__(self):
            self.executed_query = None
            self.executed_data = None

        def execute(self, query, data):
            self.executed_query = query
            self.executed_data = data

    cursor = MockCursor()

    sensor_data = (
        "SENSOR-001",
        "New York",
        25.5,
        60.0,
        3.2,
        datetime(2026, 11, 22, 1, 0, tzinfo=timezone.utc)
    )

    insert_sensor_reading(cursor, sensor_data)

    assert cursor.executed_query == INSERT_SENSOR_SQL
    assert cursor.executed_data == sensor_data
