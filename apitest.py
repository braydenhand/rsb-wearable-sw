import requests
import json
import time

# Configuration
API_BASE_URL = "https://b4aifmwd05.execute-api.us-east-1.amazonaws.com/dev"

headers = {
    "Content-Type": "application/json",
}

def test_get_vests():
    """Test GET /vests endpoint"""
    response = requests.get(f"{API_BASE_URL}/vests", headers=headers)
    print(f"GET /vests status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_create_vest():
    """Test POST /vests endpoint"""
    vest_data = {
        "name": f"Test Vest {int(time.time())}",
        "description": "Automatically created test vest",
        "is_active": True
    }
    response = requests.post(
        f"{API_BASE_URL}/vests", 
        headers=headers,
        json=vest_data
    )
    print(f"POST /vests status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_get_vest(vest_id):
    """Test GET /vests/{vest_id} endpoint"""
    response = requests.get(f"{API_BASE_URL}/vests/{vest_id}", headers=headers)
    print(f"GET /vests/{vest_id} status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_create_sensor(vest_id, sensor_type_id, position):
    """Test POST /sensors endpoint"""
    sensor_data = {
        "vest_id": vest_id,
        "sensor_type_id": sensor_type_id,
        "position": position,
        "is_active": True,
        "calibration_data": json.dumps({"offset": 0.5, "scale": 1.2})
    }
    response = requests.post(
        f"{API_BASE_URL}/sensors", 
        headers=headers,
        json=sensor_data
    )
    print(f"POST /sensors status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_get_vest_sensors(vest_id):
    """Test GET /vests/{vest_id}/sensors endpoint"""
    response = requests.get(f"{API_BASE_URL}/vests/{vest_id}/sensors", headers=headers)
    print(f"GET /vests/{vest_id}/sensors status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_add_measurements(sensor_id, vest_id):
    """Test POST /measurements endpoint"""
    # Create a batch of 5 measurements
    current_time = time.time()
    measurements = []
    
    for i in range(5):
        measurements.append({
            "sensor_id": sensor_id,
            "vest_id": vest_id,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(current_time - i)),
            "value": 20 + i * 0.5,
            "additional_data": json.dumps({"temperature": 22.5, "humidity": 40})
        })
    
    request_data = {"measurements": measurements}
    response = requests.post(
        f"{API_BASE_URL}/measurements", 
        headers=headers,
        json=request_data
    )
    print(f"POST /measurements status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_get_recent_measurements(vest_id):
    """Test GET /vests/{vest_id}/measurements/recent endpoint"""
    response = requests.get(f"{API_BASE_URL}/vests/{vest_id}/measurements/recent", headers=headers)
    print(f"GET /vests/{vest_id}/measurements/recent status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def run_full_test():
    """Run a complete test of all endpoints"""
    print("=== STARTING FULL API TEST ===")
    
    # Get existing vests
    vests = test_get_vests()
    
    # Create a new vest
    new_vest = test_create_vest()
    vest_id = new_vest.get("vest_id")
    
    # Get the vest by ID
    test_get_vest(vest_id)
    
    # Create sensors for the vest
    # Assuming sensor_type_id 1 is IMU, 2 is FlexSensor, etc.
    # You might need to adjust these IDs based on your actual data
    sensor1 = test_create_sensor(vest_id, 1, "chest")
    sensor2 = test_create_sensor(vest_id, 2, "left_shoulder")
    
    # Get all sensors for the vest
    test_get_vest_sensors(vest_id)
    
    # Add measurements for a sensor
    test_add_measurements(sensor1.get("sensor_id"), vest_id)
    
    # Get recent measurements
    test_get_recent_measurements(vest_id)
    
    print("=== API TEST COMPLETED ===")

if __name__ == "__main__":
    run_full_test()