
import sys
import json

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "kafka" / "config"))

from kafka import KafkaConsumer

from kafka_config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC,
    KAFKA_GROUP_ID
)


consumer = KafkaConsumer(

    KAFKA_TOPIC,

    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,

    group_id=KAFKA_GROUP_ID,

    auto_offset_reset="earliest",

    enable_auto_commit=True,

    key_deserializer=lambda key: (
        key.decode("utf-8") if key else None
    ),

    value_deserializer=lambda value: json.loads(
        value.decode("utf-8")
    )

)


def start_consumer():

    print("AtmoSync Kafka Consumer Started")

    try:

        for message in consumer:

            data = message.value

            print("\nNew Sensor Event Received")

            print("--------------------------------")

            print("Container:", data["container_id"])

            print("Commodity:", data["commodity"])

            print("Location:", data["location"])

            print("Temperature:", data["temperature"], "°C")

            print("Humidity:", data["humidity"], "%")

            print("Vibration:", data["vibration"])

            print("Timestamp:", data["timestamp"])

            print("Partition:", message.partition)

            print("Offset:", message.offset)

    except KeyboardInterrupt:

        print("Consumer stopped")

    finally:

        consumer.close()


if __name__ == "__main__":

    start_consumer()
