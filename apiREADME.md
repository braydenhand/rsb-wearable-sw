# Sensor Vest Database Schema

This document provides an overview of the database schema used in the Sensor Vest project. The database consists of four primary tables designed to track vests, sensor types, physical sensors, and their measurements.

## Table Overview

### 1. Vests

The `vests` table stores information about individual sensor vests.

| Column      | Type                    | Description                               |
|-------------|-------------------------|-------------------------------------------|
| vest_id     | SERIAL PRIMARY KEY      | Unique identifier for each vest           |
| name        | VARCHAR(100) NOT NULL   | Name of the vest                          |
| description | TEXT                    | Optional description of the vest          |
| created_at  | TIMESTAMP WITH TIME ZONE| Creation timestamp (defaults to current time) |
| is_active   | BOOLEAN                 | Indicates if the vest is currently active (defaults to TRUE) |

### 2. Sensor Types

The `sensor_types` table catalogs different types of sensors used in the vests.

| Column              | Type                  | Description                                |
|---------------------|------------------------|--------------------------------------------|
| sensor_type_id      | SERIAL PRIMARY KEY    | Unique identifier for each sensor type     |
| name                | VARCHAR(100) NOT NULL | Name of the sensor type (must be unique)   |
| description         | TEXT                  | Description of the sensor type             |
| unit_of_measurement | VARCHAR(50)           | Unit of measurement for the sensor readings|

Default sensor types included:
- IMU (Inertial Measurement Unit) - measured in degrees
- FlexSensor (Flexibility sensor) - measured in ohms
- StretchSensor (Stretchable sensor) - measured in ohms

### 3. Sensors

The `sensors` table tracks individual physical sensor devices installed in vests.

| Column           | Type                     | Description                                   |
|------------------|--------------------------|-----------------------------------------------|
| sensor_id        | SERIAL PRIMARY KEY       | Unique identifier for each physical sensor    |
| vest_id          | INTEGER NOT NULL         | Foreign key reference to vests.vest_id        |
| sensor_type_id   | INTEGER NOT NULL         | Foreign key reference to sensor_types.sensor_type_id |
| position         | VARCHAR(100) NOT NULL    | Position of the sensor on the vest            |
| is_active        | BOOLEAN                  | Indicates if the sensor is active (defaults to TRUE) |
| calibration_data | TEXT                     | Optional calibration data for the sensor      |
| last_maintenance | TIMESTAMP WITH TIME ZONE | Timestamp of the last maintenance performed   |

Note: Each vest can only have one sensor at any specific position (enforced by a unique constraint).

### 4. Measurements

The `measurements` table stores time-series data from sensor readings.

| Column          | Type                     | Description                              |
|-----------------|--------------------------|------------------------------------------|
| measurement_id  | BIGSERIAL PRIMARY KEY    | Unique identifier for each measurement   |
| sensor_id       | INTEGER NOT NULL         | Foreign key reference to sensors.sensor_id |
| vest_id         | INTEGER NOT NULL         | Foreign key reference to vests.vest_id   |
| timestamp       | TIMESTAMP WITH TIME ZONE | When the measurement was recorded        |
| value           | NUMERIC NOT NULL         | The measured value                       |
| additional_data | TEXT                     | Optional additional data or context      |

Note: Each sensor can only have one measurement for any specific timestamp (enforced by a unique constraint).

## Indexes

The schema includes the following indexes to optimize query performance:

1. `idx_measurements_vest_timestamp` - For fast retrieval of measurements for a specific vest ordered by timestamp
2. `idx_measurements_timestamp` - For fast retrieval of all measurements ordered by timestamp

## Relationships

- Each vest can have multiple sensors
- Each sensor must be of a defined sensor type
- Each sensor can record multiple measurements over time
- Each measurement is associated with both a specific sensor and its parent vest

# Sensor Vest API Reference

## Endpoints

### GET Operations

| Endpoint | Description | Parameters | Response |
|----------|-------------|------------|----------|
| `GET /vests` | Retrieve all vests | None | List of vest objects |
| `GET /vests/{vest_id}` | Retrieve a specific vest | `vest_id` (path) | Vest object |
| `GET /vests/{vest_id}/sensors` | Retrieve all sensors for a vest | `vest_id` (path) | List of sensor objects with type information |
| `GET /vests/{vest_id}/measurements/recent` | Retrieve recent measurements for a vest | `vest_id` (path), `seconds` (query, default: 10) | List of measurement objects with sensor position and type |

### POST Operations

| Endpoint | Description | Required Fields | Response |
|----------|-------------|----------------|----------|
| `POST /vests` | Create a new vest | `name` | Newly created vest object |
| `POST /sensors` | Create a new sensor | `vest_id`, `sensor_type_id`, `position` | Newly created sensor object |
| `POST /measurements` | Add one or more measurements | Array of objects with `sensor_id`, `value` | Added measurement objects |

## Request Examples

### Creating a Vest
```json
POST /vests
{
  "name": "Vest-Alpha",
  "description": "First prototype vest"
}
```

### Creating a Sensor
```json
POST /sensors
{
  "vest_id": 1,
  "sensor_type_id": 2,
  "position": "upper_back",
  "calibration_data": {
    "offset": 0.5,
    "multiplier": 1.2
  }
}
```

### Adding a Measurement
```json
POST /measurements
{
  "sensor_id": 3,
  "value": 42.5,
  "timestamp": "2025-03-25T15:30:00Z",
  "additional_data": {
    "ambient_temperature": 22.1
  }
}
```

### Adding Multiple Measurements (Batch)
```json
POST /measurements
[
  {
    "sensor_id": 3,
    "value": 42.5
  },
  {
    "sensor_id": 4,
    "value": 85.2
  }
]
```

## Response Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success (GET) |
| 201 | Created (POST) |
| 400 | Bad Request - Missing required fields |
| 404 | Not Found - Resource doesn't exist |
| 405 | Method Not Allowed |
| 409 | Conflict - Resource already exists |
| 500 | Internal Server Error |