
import json
import time
import random
import uuid
from datetime import datetime, timezone

containers = [
    {"id": "CONT_A", "product": "Avocado", "temp": 7.0, "humidity": 92},
    {"id": "CONT_B", "product": "Mango", "temp": 10.0, "humidity": 88},
    {"id": "CONT_C", "product": "Banana", "temp": 14.0, "humidity": 85}
]

while True:
    for container in containers:
        event = {
            "event_id": str(uuid.uuid4()),
            "container_id": container["id"],
            "product": container["product"],
            "temperature": round(
                container["temp"] + random.uniform(-1, 2), 2
            ),
            "humidity": round(
                container["humidity"] + random.uniform(-3, 3), 2
            ),
            "vibration": round(random.uniform(0.1, 1.5), 2),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        print(json.dumps(event))

    time.sleep(5)
