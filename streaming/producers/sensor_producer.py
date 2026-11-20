
import json
from confluent_kafka import Producer

from streaming.config.kafka_config import (
    KAFKA_CONFIG,
    SENSOR_TOPIC
)
from streaming.simulators.iot_simulator import generate_sensor_reading


def delivery_report(err, message):
    """Confirm whether a message reached Kafka."""

    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(
            f"Message delivered to {message.topic()} "
            f"[partition {message.partition()}]"
        )


def run_producer(total_records=10):
    """Generate sensor readings and publish them to Kafka."""

    producer = Producer(KAFKA_CONFIG)

    print("Starting AtmoSync Kafka Producer...")

    try:
        for _ in range(total_records):
            reading = generate_sensor_reading()

            producer.produce(
                topic=SENSOR_TOPIC,
                key=reading["sensor_id"],
                value=json.dumps(reading),
                callback=delivery_report
            )

            producer.poll(0)

            print(f"Sending: {reading}")

    except Exception as error:
        print(f"Producer error: {error}")

    finally:
        producer.flush()

    print("Kafka Producer Completed!")


if __name__ == "__main__":
    run_producer()
