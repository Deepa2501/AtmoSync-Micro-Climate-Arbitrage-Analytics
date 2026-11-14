
# AtmoSync - Week 1 Architecture

## Objective
Develop a simulated IoT sensor streaming pipeline
using Python and Apache Kafka.

## Components

1. Python Sensor Generator
2. Kafka Producer
3. Kafka Broker
4. container-telemetry Topic
5. Kafka Consumer

## Sensor Parameters

- Container ID
- Location
- Commodity
- Temperature
- Humidity
- Vibration
- Timestamp

## Data Flow

Python Sensor Generator
        |
        v
Kafka Producer
        |
        v
Kafka Topic
        |
        v
Kafka Consumer

## Expected Outcome

Successfully generate and stream simulated
environmental sensor measurements.
