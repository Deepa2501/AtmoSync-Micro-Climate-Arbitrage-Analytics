import json

from kafka import KafkaConsumer
from snowflake_service.connection import get_snowflake_connection

from kafka_service.config.kafka_config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC,
    KAFKA_GROUP_ID
)


consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    group_id=KAFKA_GROUP_ID,
    auto_offset_reset="earliest",
    enable_auto_commit=False,
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)


conn = get_snowflake_connection()
cursor = conn.cursor()


INSERT_QUERY = """
MERGE INTO ATMOSYNC_DB.RAW.RAW_SENSOR_EVENTS target
USING (
    SELECT
        %s AS EVENT_ID,
        %s AS CONTAINER_ID,
        %s AS LOCATION,
        %s AS COMMODITY,
        %s AS TEMPERATURE,
        %s AS HUMIDITY,
        %s AS VIBRATION,
        TO_TIMESTAMP_TZ(%s) AS EVENT_TIMESTAMP
) source
ON target.EVENT_ID = source.EVENT_ID

WHEN NOT MATCHED THEN INSERT (
    EVENT_ID,
    CONTAINER_ID,
    LOCATION,
    COMMODITY,
    TEMPERATURE,
    HUMIDITY,
    VIBRATION,
    EVENT_TIMESTAMP
)
VALUES (
    source.EVENT_ID,
    source.CONTAINER_ID,
    source.LOCATION,
    source.COMMODITY,
    source.TEMPERATURE,
    source.HUMIDITY,
    source.VIBRATION,
    source.EVENT_TIMESTAMP
)
"""


print("AtmoSync Kafka-to-Snowflake ingestion started")

try:

    for message in consumer:

        data = message.value

        values = (
            data["event_id"],
            data["container_id"],
            data["location"],
            data["commodity"],
            data["temperature"],
            data["humidity"],
            data["vibration"],
            data["timestamp"]
        )

        try:
            cursor.execute(INSERT_QUERY, values)
            conn.commit()

            # Commit Kafka offset only after Snowflake succeeds
            consumer.commit()

            print(
                "Sensor data inserted:",
                data["container_id"],
                data["temperature"]
            )

        except Exception as error:
            conn.rollback()
            print("Snowflake insertion failed:", error)
            raise

except KeyboardInterrupt:
    print("Ingestion stopped")

finally:
    cursor.close()
    conn.close()
    consumer.close()