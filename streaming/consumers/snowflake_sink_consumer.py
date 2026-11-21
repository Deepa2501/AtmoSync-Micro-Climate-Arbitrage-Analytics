
"""
AtmoSync Kafka-to-Snowflake Sink Consumer.

Consumes IoT sensor readings from Kafka, validates them,
and stores valid records in Snowflake RAW_SENSOR_DATA.
"""

import json
import math
from datetime import datetime, timezone

from confluent_kafka import Consumer, KafkaException

from streaming.config.kafka_config import KAFKA_CONFIG, SENSOR_TOPIC
from config.snowflake_connection import get_snowflake_connection


SINK_CONSUMER_GROUP_ID = "atmosync-snowflake-sink"

INSERT_SENSOR_SQL = """
    INSERT INTO ATMOSYNC_DB.RAW.RAW_SENSOR_DATA (
        SENSOR_ID,
        LOCATION,
        TEMPERATURE,
        HUMIDITY,
        VIBRATION,
        SENSOR_TIMESTAMP
    )
    VALUES (%s, %s, %s, %s, %s, %s)
"""


def validate_sensor_reading(data):
    """Validate and normalize an incoming sensor reading."""

    if not isinstance(data, dict):
        raise ValueError("Sensor message must be a JSON object.")

    required_fields = [
        "sensor_id",
        "location",
        "temperature",
        "humidity",
        "vibration",
        "timestamp"
    ]

    missing = [field for field in required_fields if field not in data]

    if missing:
        raise ValueError(f"Missing fields: {', '.join(missing)}")

    for field in ("sensor_id", "location"):
        if not isinstance(data[field], str) or not data[field].strip():
            raise ValueError(f"Invalid {field}")

    numeric_values = {}

    for field in ("temperature", "humidity", "vibration"):
        value = data[field]

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Invalid numeric field: {field}")

        if not math.isfinite(value):
            raise ValueError(f"Non-finite value: {field}")

        numeric_values[field] = float(value)

    timestamp = data["timestamp"]

    if not isinstance(timestamp, str):
        raise ValueError("Timestamp must be a string.")

    try:
        parsed_timestamp = datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )
    except ValueError as error:
        raise ValueError("Invalid sensor timestamp.") from error

    if parsed_timestamp.tzinfo is None:
        raise ValueError("Timestamp must include timezone information.")

    return (
        data["sensor_id"].strip(),
        data["location"].strip(),
        numeric_values["temperature"],
        numeric_values["humidity"],
        numeric_values["vibration"],
        parsed_timestamp.astimezone(timezone.utc)
    )


def insert_sensor_reading(cursor, sensor_data):
    """Insert one validated sensor reading into Snowflake."""

    cursor.execute(INSERT_SENSOR_SQL, sensor_data)


def run_sink_consumer(total_records=10):
    """Consume Kafka messages and insert them into Snowflake."""

    consumer = None
    connection = None
    cursor = None
    received = 0
    inserted = 0
    rejected = 0

    try:
        connection = get_snowflake_connection()
        cursor = connection.cursor()

        consumer_config = {
            **KAFKA_CONFIG,
            "group.id": SINK_CONSUMER_GROUP_ID,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "enable.auto.offset.store": False
        }

        consumer = Consumer(consumer_config)
        consumer.subscribe([SENSOR_TOPIC])

        print("Starting AtmoSync Snowflake Sink Consumer...")
        print(f"Listening to topic: {SENSOR_TOPIC}")

        while received < total_records:
            message = consumer.poll(2.0)

            if message is None:
                continue

            if message.error():
                raise KafkaException(message.error())

            try:
                raw_data = json.loads(
                    message.value().decode("utf-8")
                )

                sensor_data = validate_sensor_reading(raw_data)

            except (ValueError, UnicodeDecodeError) as error:
                print(f"Rejected invalid message: {error}")

                # Skip malformed messages to avoid repeatedly
                # processing the same invalid record.
                consumer.commit(
                    message=message,
                    asynchronous=False
                )

                rejected += 1
                received += 1
                continue

            # Insert into Snowflake before committing Kafka offset.
            insert_sensor_reading(cursor, sensor_data)
            connection.commit()

            consumer.commit(
                message=message,
                asynchronous=False
            )

            inserted += 1
            received += 1

            print(
                f"Inserted sensor reading: {sensor_data[0]}"
            )

    except KeyboardInterrupt:
        print("Sink consumer interrupted.")

    finally:
        if consumer is not None:
            consumer.close()

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

        print("\nSnowflake Sink Consumer completed.")
        print(f"Messages processed: {received}")
        print(f"Records inserted: {inserted}")
        print(f"Messages rejected: {rejected}")


if __name__ == "__main__":
    run_sink_consumer()
