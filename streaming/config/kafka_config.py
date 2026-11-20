
from config.settings import KAFKA_BOOTSTRAP_SERVERS

# Kafka broker configuration
KAFKA_CONFIG = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS
}

# Kafka topic for IoT sensor readings
SENSOR_TOPIC = "iot.sensor.readings"

# Consumer group
CONSUMER_GROUP_ID = "atmosync-sensor-consumer"
