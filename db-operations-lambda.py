import os
import json
import psycopg2
import psycopg2.extras
import logging
from datetime import datetime, timedelta
from collections import defaultdict
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_db_connection():
    """Create and return a database connection"""
    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        database=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD']
    )
    # Set autocommit to true to avoid transaction issues
    conn.autocommit = True
    return conn

def lambda_handler(event, context):
    """
    Lambda function to handle GET and PUT operations for the sensor vest project.
    Routes to appropriate handler based on HTTP method and path.
    """
    try:
        http_method = event['httpMethod']
        path = event['path']
        
        # Parse path components
        path_parts = path.strip('/').split('/')
        
        # Route to appropriate handler
        if http_method == 'GET':
            return handle_get(event, path_parts)
        elif http_method == 'POST' or http_method == 'PUT':
            return handle_put(event, path_parts)
        else:
            return {
                'statusCode': 405,
                'body': json.dumps({'error': 'Method not allowed'})
            }
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }

def handle_get(event, path_parts):
    """Handle GET requests"""
    
    # GET /vests - List all vests
    if len(path_parts) == 1 and path_parts[0] == 'vests':
        return get_all_vests()
    
    # GET /vests/{vest_id} - Get a specific vest
    elif len(path_parts) == 2 and path_parts[0] == 'vests':
        vest_id = path_parts[1]
        return get_vest(vest_id)
    
    # GET /vests/{vest_id}/sensors - Get all sensors for a vest
    elif len(path_parts) == 3 and path_parts[0] == 'vests' and path_parts[2] == 'sensors':
        vest_id = path_parts[1]
        return get_vest_sensors(vest_id)
    
    # GET /vests/{vest_id}/measurements/recent - Get recent measurements for a vest
    elif len(path_parts) == 4 and path_parts[0] == 'vests' and path_parts[2] == 'measurements' and path_parts[3] == 'recent':
        vest_id = path_parts[1]
        query_params = event.get('queryStringParameters') or {}
        seconds = int(query_params.get('seconds', 10))
        return get_recent_measurements(vest_id, seconds)
    
    # Unsupported path
    else:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Not found'})
        }

def handle_put(event, path_parts):
    """Handle POST/PUT requests"""
    
    # Load the request body
    body = json.loads(event.get('body', '{}'))
    
    # POST /vests - Create a new vest
    if len(path_parts) == 1 and path_parts[0] == 'vests':
        return create_vest(body)
    
    # POST /sensors - Create a new sensor
    elif len(path_parts) == 1 and path_parts[0] == 'sensors':
        return create_sensor(body)
    
    # POST /measurements - Add measurement(s)
    elif len(path_parts) == 1 and path_parts[0] == 'measurements':
        return add_measurements(body)
    
    # Unsupported path
    else:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'Not found'})
        }

# GET handlers
def get_all_vests():
    """Get all vests"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM vests ORDER BY vest_id")
            results = cur.fetchall()
            return {
                'statusCode': 200,
                'body': json.dumps(results, default=str)
            }
    finally:
        conn.close()

def get_vest(vest_id):
    """Get a specific vest by ID"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM vests WHERE vest_id = %s", (vest_id,))
            result = cur.fetchone()
            
            if result:
                return {
                    'statusCode': 200,
                    'body': json.dumps(result, default=str)
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Vest not found'})
                }
    finally:
        conn.close()

def get_vest_sensors(vest_id):
    """Get all sensors for a specific vest"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT s.*, st.name as sensor_type_name, st.unit_of_measurement 
                FROM sensors s
                JOIN sensor_types st ON s.sensor_type_id = st.sensor_type_id
                WHERE s.vest_id = %s
                ORDER BY s.sensor_id
            """, (vest_id,))
            results = cur.fetchall()
            
            return {
                'statusCode': 200,
                'body': json.dumps(results, default=str)
            }
    finally:
        conn.close()

def get_recent_measurements(vest_id, seconds=10):
    """Get recent measurements for a vest from the last X seconds"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT m.*, s.position, st.name as sensor_type
                FROM measurements m
                JOIN sensors s ON m.sensor_id = s.sensor_id
                JOIN sensor_types st ON s.sensor_type_id = st.sensor_type_id
                WHERE m.vest_id = %s 
                AND m.timestamp > NOW() - INTERVAL '%s seconds'
                ORDER BY m.timestamp DESC, s.position
            """, (vest_id, seconds))
            results = cur.fetchall()
            
            return {
                'statusCode': 200,
                'body': json.dumps(results, default=str)
            }
    finally:
        conn.close()

# POST handlers
def create_vest(data):
    """Create a new vest"""
    required_fields = ['name']
    for field in required_fields:
        if field not in data:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Missing required field: {field}'})
            }
    
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO vests (name, description)
                VALUES (%s, %s)
                RETURNING vest_id, name, description, created_at, is_active
            """, (data['name'], data.get('description')))
            
            result = cur.fetchone()
            
            return {
                'statusCode': 201,
                'body': json.dumps(result, default=str)
            }
    finally:
        conn.close()

def create_sensor(data):
    """Create a new sensor"""
    required_fields = ['vest_id', 'sensor_type_id', 'position']
    for field in required_fields:
        if field not in data:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Missing required field: {field}'})
            }
    
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Check if vest exists
            cur.execute("SELECT vest_id FROM vests WHERE vest_id = %s", (data['vest_id'],))
            if not cur.fetchone():
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Vest not found'})
                }
                
            # Check if sensor type exists
            cur.execute("SELECT sensor_type_id FROM sensor_types WHERE sensor_type_id = %s", 
                       (data['sensor_type_id'],))
            if not cur.fetchone():
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Sensor type not found'})
                }
            
            # Create sensor
            cur.execute("""
                INSERT INTO sensors (vest_id, sensor_type_id, position, calibration_data)
                VALUES (%s, %s, %s, %s)
                RETURNING sensor_id, vest_id, sensor_type_id, position, is_active, calibration_data, last_maintenance
            """, (
                data['vest_id'], 
                data['sensor_type_id'], 
                data['position'],
                json.dumps(data.get('calibration_data', {}))
            ))
            
            result = cur.fetchone()
            
            return {
                'statusCode': 201,
                'body': json.dumps(result, default=str)
            }
    except psycopg2.IntegrityError as e:
        if "unique_measurement" in str(e):
            return {
                'statusCode': 409,
                'body': json.dumps({'error': 'A sensor at this position already exists on this vest'})
            }
        else:
            raise
    finally:
        conn.close()
def add_measurements(data):
    """Add one or more measurements with linearly interpolated timestamps"""
    import json
    import psycopg2.extras
    from datetime import datetime, timedelta
    from collections import defaultdict

    # Check if single measurement or batch
    measurements = data if isinstance(data, list) else [data]
    
    # Validate measurements
    for measurement in measurements:
        required_fields = ['sensor_id', 'value']
        for field in required_fields:
            if field not in measurement:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': f'Missing required field: {field}'})
                }

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Group measurements by sensor ID
            sensor_groups = defaultdict(list)
            sensor_vest_ids = {}
            
            # First, get the vest_id for each measurement's sensor
            for measurement in measurements:
                # If we haven't looked up this sensor yet
                if measurement['sensor_id'] not in sensor_vest_ids:
                    # Get vest_id for the sensor
                    cur.execute("SELECT vest_id FROM sensors WHERE sensor_id = %s", 
                                (measurement['sensor_id'],))
                    sensor_result = cur.fetchone()

                    if not sensor_result:
                        return {
                            'statusCode': 404,
                            'body': json.dumps({'error': f'Sensor with ID {measurement["sensor_id"]} not found'})
                        }
                    
                    # Store the vest_id for this sensor
                    sensor_vest_ids[measurement['sensor_id']] = sensor_result['vest_id']
                
                # Group by sensor_id
                sensor_groups[measurement['sensor_id']].append(measurement)
            
            # Calculate timestamps for each sensor group
            current_time = datetime.now()
            results = []
            
            for sensor_id, group in sensor_groups.items():
                # Calculate interval based on number of measurements
                num_measurements = len(group)
                if num_measurements == 1:
                    # If only one measurement, use current time
                    group[0]['timestamp'] = current_time
                else:
                    # Calculate time interval (30 seconds / (num_measurements - 1))
                    interval_seconds = 30.0 / (num_measurements - 1)
                    
                    # Start time is 30 seconds ago
                    start_time = current_time - timedelta(seconds=30)
                    
                    # Assign timestamps
                    for i, measurement in enumerate(group):
                        interpolated_time = start_time + timedelta(seconds=i * interval_seconds)
                        measurement['timestamp'] = interpolated_time
            
            # Now insert all measurements with their calculated timestamps
            for measurement in measurements:
                # Get the vest_id we already looked up
                vest_id = sensor_vest_ids[measurement['sensor_id']]
                
                # Insert measurement
                cur.execute("""
                    INSERT INTO measurements (sensor_id, vest_id, timestamp, value, additional_data)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING measurement_id, sensor_id, vest_id, timestamp, value, additional_data
                """, (
                    measurement['sensor_id'],
                    vest_id,
                    measurement['timestamp'],
                    measurement['value'],
                    json.dumps(measurement.get('additional_data', {}))
                ))
                
                results.append(cur.fetchone())
            
            # Commit the transaction
            conn.commit()
                
            return {
                'statusCode': 201,
                'body': json.dumps({'message': 'Measurements added successfully'}, default=str)
            }
    except Exception as e:
        # Log the error for debugging
        print(f"Error in add_measurements: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }
    except psycopg2.IntegrityError as e:
        if "unique_measurement" in str(e):
            return {
                'statusCode': 409,
                'body': json.dumps({'error': 'A measurement for this sensor at this timestamp already exists'})
            }
        else:
            # Log the error for debugging
            print(f"Database integrity error: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Database error: {str(e)}'})
            }
    finally:
        conn.close()