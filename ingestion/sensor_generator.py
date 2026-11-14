
import random
import uuid
import json
import time

from datetime import datetime, timezone


# Container configuration
CONTAINERS = {
    "CONT001": {
        "location": "Nashik",
        "commodity": "Tomato"
    },
    "CONT002": {
        "location": "Pune",
        "commodity": "Onion"
    },
    "CONT003": {
        "location": "Mumbai",
        "commodity": "Apple"
    }
}


def generate_sensor_data(container_id):

    container = CONTAINERS[container_id]

    temperature = round(random.uniform(5, 40), 2)
    humidity = round(random.uniform(30, 95), 2)
    vibration = round(random.uniform(0.1, 5.0), 2)

    sensor_data = {

        "event_id": str(uuid.uuid4()),

        "container_id": container_id,

        "location": container["location"],

        "commodity": container["commodity"],

        "temperature": temperature,

        "humidity": humidity,

        "vibration": vibration,

        "timestamp": datetime.now(
            timezone.utc
        ).isoformat()

    }

    return sensor_data


if __name__ == "__main__":

    print("AtmoSync IoT Sensor Generator Started")

    try:

        while True:

            for container_id in CONTAINERS:

                data = generate_sensor_data(container_id)

                print(json.dumps(data, indent=4))

            time.sleep(5)

    except KeyboardInterrupt:

        print("Sensor Generator Stopped")
