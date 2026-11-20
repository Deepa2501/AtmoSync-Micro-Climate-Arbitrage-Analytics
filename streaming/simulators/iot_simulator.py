
import random
import time
from datetime import datetime, timezone


def generate_sensor_reading():
    """Generate a sample IoT sensor reading."""

    return {
        "sensor_id": f"SENSOR-{random.randint(1, 5):03d}",
        "location": random.choice(
            ["New York", "Los Angeles", "Chicago"]
        ),
        "temperature": round(random.uniform(15, 40), 2),
        "humidity": round(random.uniform(30, 90), 2),
        "vibration": round(random.uniform(0, 10), 2),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def run_simulator(interval=2, total_records=10):
    """Generate sensor readings at regular intervals."""

    print("Starting AtmoSync IoT Sensor Simulator...")

    for _ in range(total_records):
        reading = generate_sensor_reading()

        print(reading)

        time.sleep(interval)

    print("IoT Sensor Simulation Completed!")


if __name__ == "__main__":
    run_simulator()
