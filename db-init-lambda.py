import os
import psycopg2
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function to initialize the database schema for the sensor vest project.
    This should be run once to set up the database tables.
    """
    try:
        # Get database connection parameters from environment variables
        db_host = os.environ['DB_HOST']
        db_name = os.environ['DB_NAME']
        db_user = os.environ['DB_USER']
        db_password = os.environ['DB_PASSWORD']
        
        # Connect to the database
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        # Create a cursor
        cur = conn.cursor()
        
        # Create tables
        create_tables_sql = """
        -- Table for vests
        CREATE TABLE IF NOT EXISTS vests (
            vest_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            is_active BOOLEAN DEFAULT TRUE
        );

        -- Table for sensor types
        CREATE TABLE IF NOT EXISTS sensor_types (
            sensor_type_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            unit_of_measurement VARCHAR(50)
        );

        -- Table for sensors (physical devices)
        CREATE TABLE IF NOT EXISTS sensors (
            sensor_id SERIAL PRIMARY KEY,
            vest_id INTEGER NOT NULL REFERENCES vests(vest_id),
            sensor_type_id INTEGER NOT NULL REFERENCES sensor_types(sensor_type_id),
            position VARCHAR(100) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            calibration_data TEXT,
            last_maintenance TIMESTAMP WITH TIME ZONE,
            UNIQUE(vest_id, position)
        );

        -- Table for sensor measurements (time-series data)
        CREATE TABLE IF NOT EXISTS measurements (
            measurement_id BIGSERIAL PRIMARY KEY,
            sensor_id INTEGER NOT NULL REFERENCES sensors(sensor_id),
            vest_id INTEGER NOT NULL REFERENCES vests(vest_id),
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
            value NUMERIC NOT NULL,
            additional_data TEXT,
            CONSTRAINT unique_measurement UNIQUE (sensor_id, timestamp)
        );

        -- Create indexes for fast queries
        CREATE INDEX IF NOT EXISTS idx_measurements_vest_timestamp 
        ON measurements(vest_id, timestamp DESC);
        
        CREATE INDEX IF NOT EXISTS idx_measurements_timestamp 
        ON measurements(timestamp DESC);
        """
        
        # Execute the SQL statements
        cur.execute(create_tables_sql)
        
        # Insert default sensor types
        insert_sensor_types_sql = """
        INSERT INTO sensor_types (name, description, unit_of_measurement)
        VALUES 
            ('IMU', 'Inertial Measurement Unit', 'degrees'),
            ('FlexSensor', 'Flexibility sensor', 'ohms'),
            ('StretchSensor', 'Stretchable sensor', 'ohms')
        ON CONFLICT (name) DO NOTHING;
        """
        
        # We'll need to modify this to avoid conflict on name
        # Since we didn't create a unique constraint on name, let's check first
        cur.execute("ALTER TABLE sensor_types ADD CONSTRAINT unique_sensor_type_name UNIQUE (name);")
        conn.commit()
        
        # Now we can use the ON CONFLICT clause
        cur.execute(insert_sensor_types_sql)
        
        # Commit the transaction
        conn.commit()
        
        # Close cursor and connection
        cur.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'body': json.dumps('Database initialized successfully!')
        }
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error initializing database: {str(e)}')
        }