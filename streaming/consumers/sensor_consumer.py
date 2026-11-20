
import json
from confluent_kafka import Consumer, KafkaException

from streaming.config.kafka_config import (
    KAFKA_CONFIG,
    SENSOR_TOPIC,
    CONSUMER_GROUP_ID
)


def run_consumer(total_records=10):
    """Read sensor messages from Kafka."""

    consumer_config = {
        **KAFKA_CONFIG,
        "group.id": CONSUMER_GROUP_ID,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True
    }

    consumer = Consumer(consumer_config)

    consumer.subscribe([SENSOR_TOPIC])

    print("Starting AtmoSync Kafka Consumer...")
    print(f"Listening to topic: {SENSOR_TOPIC}")

    received = 0

    try:
        while received < total_records:
            message = consumer.poll(2.0)

            if message is None:
                continue

            if message.error():
                raise KafkaException(message.error())

            sensor_data = json.loads(message.value().decode("utf-8"))

            print("\nReceived Sensor Data:")
            print(json.dumps(sensor_data, indent=4))

            received += 1

    except KeyboardInterrupt:
        print("Consumer interrupted.")

    finally:
        consumer.close()
        print(f"\nConsumer completed. Messages received: {received}")


if __name__ == "__main__":
    run_consumer()
