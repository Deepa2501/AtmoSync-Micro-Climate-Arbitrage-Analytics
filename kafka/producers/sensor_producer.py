
import sys
import json
import time

from pathlib import Path

# Add project root to Python path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "kafka" / "config"))

from kafka import KafkaProducer
from ingestion.sensor_generator import (
    generate_sensor_data,
    CONTAINERS
)
from kafka_config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC
)


producer = KafkaProducer(

    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,

    key_serializer=lambda key: key.encode("utf-8"),

    value_serializer=lambda value: json.dumps(
        value
    ).encode("utf-8"),

    acks="all",

    retries=5

)


def start_producer():

    print("AtmoSync Kafka Producer Started")

    try:

        while True:

            for container_id in CONTAINERS:

                data = generate_sensor_data(container_id)

                future = producer.send(
                    KAFKA_TOPIC,
                    key=container_id,
                    value=data
                )

                metadata = future.get(timeout=10)

                print(
                    f"Sent: {container_id} | "
                    f"Partition: {metadata.partition} | "
                    f"Offset: {metadata.offset}"
                )

            time.sleep(5)

    except KeyboardInterrupt:

        print("Producer stopped")

    finally:

        producer.flush()
        producer.close()


if __name__ == "__main__":

    start_producer()
