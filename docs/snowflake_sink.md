
# AtmoSync Kafka-to-Snowflake Sink Consumer

## Overview

The Snowflake Sink Consumer is responsible for transferring IoT sensor readings from Apache Kafka into Snowflake.

### Data Flow

IoT Simulator → Kafka Producer → Kafka Topic → Snowflake Sink Consumer → Snowflake RAW_SENSOR_DATA

## Components

- `streaming/simulators/iot_simulator.py`: Generates simulated sensor readings.
- `streaming/producers/sensor_producer.py`: Publishes readings to Kafka.
- `streaming/consumers/snowflake_sink_consumer.py`: Consumes, validates, and inserts readings into Snowflake.
- `snowflake/tables/create_sensor_table.sql`: Defines the raw sensor data table.
- `tests/test_snowflake_sink.py`: Tests validation and database insertion logic.

## Database Setup

Execute the following SQL file in Snowflake:

`snowflake/tables/create_sensor_table.sql`

It creates:

`ATMOSYNC_DB.RAW.RAW_SENSOR_DATA`

The table stores:
- Sensor ID
- Location
- Temperature
- Humidity
- Vibration
- Sensor timestamp
- Ingestion timestamp

## Configuration

Configure the required Kafka and Snowflake credentials in your local `.env` file.

Never commit `.env` or private keys to Git.

Kafka broker configuration:
- `KAFKA_BOOTSTRAP_SERVERS`
- `KAFKA_SENSOR_TOPIC`

Snowflake configuration:
- Account
- User
- Password
- Warehouse
- Database
- Schema

## Running the Consumer

Start the Kafka broker and ensure the sensor topic is available.

Run the producer:

```bash
python -m streaming.producers.sensor_producer
```

Run the Snowflake sink consumer:

```bash
python -m streaming.consumers.snowflake_sink_consumer
```

## Validation and Error Handling

The consumer validates:
- Required message fields
- Sensor ID and location
- Numeric sensor values
- Finite numeric values
- Valid timezone-aware timestamps

Invalid messages are rejected instead of being inserted.

Valid records are inserted using parameterized SQL queries.

Kafka offsets are committed after successful Snowflake insertion and database commit.

## Testing

Run the sink consumer tests:

```bash
python -m pytest tests/test_snowflake_sink.py -v
```

Run the configured project test suite:

```bash
python -m pytest -v
```

## Integration Testing

Live end-to-end testing requires:
- A running Kafka broker
- A configured Kafka topic
- Valid Snowflake credentials
- The RAW_SENSOR_DATA table created in Snowflake

Unit tests can run independently using mocked database operations.
