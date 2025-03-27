import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import time
import plotly.express as px
from datetime import datetime

API_BASE_URL = "https://b4aifmwd05.execute-api.us-east-1.amazonaws.com/dev"
headers = {
    "Content-Type": "application/json",
}

# Initialize session state variables for login functionality
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# App title
st.title("🥊 Rock Steady Boxing Dashboard")

# Function to handle login
def login(username, password):
    # For simplicity, we're using a hardcoded user list
    # * is admin account that can see all vests
    valid_users = {
        "1": "password1",
        "2": "password2",
        "3": "password3",
        "*": "*"
    }
    
    if username in valid_users and password == valid_users[username]:
        st.session_state.logged_in = True
        st.session_state.username = username
        return True
    return False

# Function to handle logout
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    # Clear selected vest on logout
    if "selected_vest" in st.session_state:
        del st.session_state["selected_vest"]

# Login form
if not st.session_state.logged_in:
    st.header("Login")
    with st.form("login_form"):
        username = st.text_input("User ID")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if login(username, password):
                st.success(f"Welcome, User {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password")
else:
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "Vest Dashboard", "Settings"])
    
    # Logout button in sidebar
    if st.sidebar.button("Logout"):
        logout()
        st.rerun()
    
    # Display current user
    st.sidebar.write(f"Logged in as User: {st.session_state.username}")

    # Function to get all vests
    def get_all_vests():
        try:
            response = requests.get(f"{API_BASE_URL}/vests", headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to fetch vests. Status code: {response.status_code}")
                return []
        except Exception as e:
            st.error(f"Error fetching vests: {str(e)}")
            return []

    # Function to get a specific vest
    def get_vest(vest_id):
        try:
            response = requests.get(f"{API_BASE_URL}/vests/{vest_id}", headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to fetch vest. Status code: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Error fetching vest: {str(e)}")
            return None

    # Function to get sensors for a vest
    def get_vest_sensors(vest_id):
        try:
            response = requests.get(f"{API_BASE_URL}/vests/{vest_id}/sensors", headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to fetch sensors. Status code: {response.status_code}")
                return []
        except Exception as e:
            st.error(f"Error fetching sensors: {str(e)}")
            return []

    # Function to get recent measurements for a vest
    def get_recent_measurements(vest_id):
        try:
            response = requests.get(f"{API_BASE_URL}/vests/{vest_id}/measurements/recent?seconds=10000000", headers=headers)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 500:
                # Handle potential error with the endpoint
                st.warning("The measurements API is currently experiencing issues. Displaying sample data instead.")
                # Return simulated data for development
                return generate_sample_measurements(vest_id)
            else:
                st.error(f"Failed to fetch measurements. Status code: {response.status_code}")
                return []
        except Exception as e:
            st.error(f"Error fetching measurements: {str(e)}")
            return []

    # Function to generate sample measurements for development when API fails
    def generate_sample_measurements(vest_id):
        sensors = get_vest_sensors(vest_id)
        if not sensors:
            return []
            
        sample_data = []
        current_time = time.time()
        
        for sensor in sensors:
            # Generate 10 sample measurements for each sensor
            for i in range(10):
                timestamp = datetime.fromtimestamp(current_time - i * 3600)  # One hour intervals
                sample_data.append({
                    "measurement_id": i,
                    "sensor_id": sensor.get("sensor_id"),
                    "vest_id": vest_id,
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "value": 20 + np.random.normal(0, 5),  # Random value around 20
                    "position": sensor.get("position", "unknown"),
                    "sensor_type": sensor.get("sensor_type", "unknown"),
                    "additional_data": {"simulated": True}
                })
        
        return sample_data

    # Function to add new measurements for a sensor
    def add_measurement(sensor_id, value):
        try:
            # Create measurement data
            measurement = {
                "sensor_id": sensor_id,
                "value": value,
                "additional_data": {"source": "dashboard"}
            }
            
            # Try both API formats - with and without wrapper
            try:
                # First try with the measurements wrapper
                request_data = {"measurements": [measurement]}
                response = requests.post(
                    f"{API_BASE_URL}/measurements", 
                    headers=headers,
                    json=request_data
                )
                
                if response.status_code >= 400:
                    # If that fails, try direct format
                    response = requests.post(
                        f"{API_BASE_URL}/measurements", 
                        headers=headers,
                        json=[measurement]  # Send as direct list
                    )
                    
                    # If that fails too, try single object
                    if response.status_code >= 400:
                        response = requests.post(
                            f"{API_BASE_URL}/measurements", 
                            headers=headers,
                            json=measurement  # Send as single object
                        )
            except Exception as e:
                st.error(f"Error adding measurement: {str(e)}")
                return False
            
            if response.status_code in [200, 201]:
                return True
            else:
                st.error(f"Failed to add measurement. Status code: {response.status_code}")
                if response.text:
                    st.error(f"Response: {response.text}")
                return False
        except Exception as e:
            st.error(f"Error adding measurement: {str(e)}")
            return False

    # Function to format measurements data for plotting
    def format_measurements_data(measurements):
        if not measurements:
            return pd.DataFrame()
        
        formatted_data = []
        for m in measurements:
            # Parse timestamp
            try:
                timestamp = datetime.strptime(m.get("timestamp"), "%Y-%m-%d %H:%M:%S")
            except:
                # Try another format if the first one fails
                try:
                    timestamp = datetime.fromisoformat(m.get("timestamp").replace('Z', '+00:00'))
                except:
                    timestamp = datetime.now()  # Fallback
                
            formatted_data.append({
                "sensor_id": m.get("sensor_id"),
                "timestamp": timestamp,
                "value": float(m.get("value", 0)),  # Ensure value is float
                "position": m.get("position", "unknown"),
                "sensor_type": m.get("sensor_type", "unknown")
            })
        
        return pd.DataFrame(formatted_data)

    # Home Page
    if page == "Home":
        st.header(f"Welcome to the Rock Steady Sensor Dashboard, User {st.session_state.username}")
        st.write("This dashboard displays real-time sensor data from your boxing vest.")
        st.write("Use the navigation on the left to view vest data or change settings.")
        
        # Get all vests and filter for the logged-in user's vest ID
        all_vests = get_all_vests()
        user_vest_id = st.session_state.username  # Using username as vest_id filter
        if user_vest_id == "*":
            user_vests = all_vests
        else:
        # Filter vests for the current user
            user_vests = [v for v in all_vests if str(v.get("vest_id")) == user_vest_id]
        
        active_vests = [v for v in user_vests if v.get("is_active", False)]
        
        st.metric("Your Active Vests", len(active_vests))
        
        # Show the user's vests
        if user_vests:
            st.subheader("Your Vests")
            vest_df = pd.DataFrame([{
                "Vest ID": v.get("vest_id"),
                "Name": v.get("name"),
                "Status": "Active" if v.get("is_active", False) else "Inactive"
            } for v in user_vests])
            
            st.dataframe(vest_df)
        else:
            st.info(f"No vests found with ID {user_vest_id}.")

 # Vest Dashboard Page
    elif page == "Vest Dashboard":
        st.header("📈 Vest Dashboard")
        
        # Get all vests and filter for the logged-in user
        all_vests = get_all_vests()
        user_vest_id = st.session_state.username  # Using username as vest_id filter
        
        # Special case for "*" user who can see all vests
        if user_vest_id == "*":
            user_vests = all_vests
        else:
            # Filter vests for the current user
            user_vests = [v for v in all_vests if str(v.get("vest_id")) == user_vest_id]
        
        if not user_vests:
            st.warning(f"No vests found for User {st.session_state.username}. Please check your API connection.")
        else:
            # If not in detailed view, show user's vests
            if "selected_vest" not in st.session_state:
                # Layout for vest cards
                vest_cards = []
                for i, vest in enumerate(user_vests):
                    # Only show active vests by default
                    if vest.get("is_active", False):
                        vest_cards.append(vest)
                
                # Show toggle for inactive vests
                show_inactive = st.checkbox("Show Inactive Vests")
                if show_inactive:
                    vest_cards = user_vests
                
                # Create a 3-column layout for vest cards
                cols = st.columns(3)
                for i, vest in enumerate(vest_cards):
                    with cols[i % 3]:
                        # Create a card-like container
                        with st.container():
                            st.subheader(vest.get("name", f"Vest {vest.get('vest_id')}"))
                            st.caption(f"ID: {vest.get('vest_id')}")
                            
                            # Status indicator
                            status = "🟢 Active" if vest.get("is_active", False) else "🔴 Inactive"
                            st.caption(status)
                            
                            # Get sensors for this vest
                            sensors = get_vest_sensors(vest.get("vest_id"))
                            
                            # Show sensor count
                            sensor_count = len(sensors) if sensors else 0
                            st.caption(f"Sensors: {sensor_count}")
                            
                            # Description
                            st.write(vest.get("description", "No description"))
                            
                            # Button to view details
                            if st.button(f"View Details", key=f"vest_{vest.get('vest_id')}"):
                                st.session_state["selected_vest"] = vest.get("vest_id")
                                st.rerun()

    # Settings Page
    elif page == "Settings":
        st.header("⚙️ Settings")
        st.write("Modify your preferences here.")
        
        # API settings
        st.subheader("API Configuration")
        api_url = st.text_input("API Base URL", value=API_BASE_URL)
        
        if st.button("Save Settings"):
            API_BASE_URL = api_url
            st.success("Settings saved successfully!")
        
        # Test connection
        if st.button("Test API Connection"):
            try:
                response = requests.get(f"{api_url}/vests", headers=headers)
                if response.status_code == 200:
                    st.success(f"Connection successful! Found {len(response.json())} vests.")
                else:
                    st.error(f"Connection failed with status code: {response.status_code}")
            except Exception as e:
                st.error(f"Connection error: {str(e)}")

    # Vest Detail Page
    if "selected_vest" in st.session_state:
        vest_id = st.session_state["selected_vest"]
        
        # Verify the vest belongs to the logged-in user
        if str(vest_id) != st.session_state.username and st.session_state.username != "*":
            st.error("You don't have permission to view this vest.")
            del st.session_state["selected_vest"]
            st.rerun()
        
        # Get vest details
        vest = get_vest(vest_id)
        
        if not vest:
            st.error("Failed to load vest details")
            if st.button("Back to Vest Dashboard"):
                del st.session_state["selected_vest"]
                st.rerun()
        else:
            # Vest header with back button
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                st.header(f"📊 {vest.get('name', f'Vest {vest_id}')} Details")
            with col2:
                if st.button("Back to Dashboard", key="back_button"):
                    del st.session_state["selected_vest"]
                    st.rerun()
            
            # Vest metadata
            st.caption(f"ID: {vest_id} | Status: {'Active' if vest.get('is_active', False) else 'Inactive'}")
            
            # Get sensors for this vest
            sensors = get_vest_sensors(vest_id)
            
            if not sensors:
                st.warning("No sensors found for this vest")
            else:
                # Get measurements
                measurements = get_recent_measurements(vest_id)
                measurements_df = format_measurements_data(measurements)
                
                # Create tabs for different views
                tab1, tab2, tab3 = st.tabs(["Sensors Overview", "Measurements Data", "Add Data"])
                
                with tab1:
                    # Create a table showing sensor details
                    sensor_df = pd.DataFrame([{
                        "Sensor ID": s.get("sensor_id"),
                        "Type": s.get("sensor_type"),
                        "Position": s.get("position"),
                        "Status": "Active" if s.get("is_active", False) else "Inactive",
                    } for s in sensors])
                    
                    st.dataframe(sensor_df)
                    
                    # Show graphs for each sensor
                    st.subheader("Sensor Measurements")
                    
                    if measurements_df.empty:
                        st.info("No recent measurements available for this vest")
                    else:
                        # Group by sensor_id
                        sensor_ids = measurements_df["sensor_id"].unique()
                        
                        for sensor_id in sensor_ids:
                            # Find the matching sensor info
                            sensor_info = next((s for s in sensors if s.get("sensor_id") == sensor_id), {})
                            sensor_type = sensor_info.get("sensor_type", "Unknown Type")
                            position = sensor_info.get("position", "Unknown Position")
                            
                            # Filter data for this sensor
                            sensor_data = measurements_df[measurements_df["sensor_id"] == sensor_id]
                            
                            if not sensor_data.empty:
                                # Create a card-like container for each sensor
                                st.subheader(f"{sensor_type} at {position}")
                                
                                # Create an interactive time series plot
                                fig = px.line(
                                    sensor_data,
                                    x="timestamp",
                                    y="value",
                                    title=f"Sensor ID: {sensor_id}"
                                )
                                st.plotly_chart(fig, use_container_width=True)
                
                with tab2:
                    # Show raw data
                    if measurements_df.empty:
                        st.info("No measurement data available")
                    else:
                        st.dataframe(measurements_df)
                
                with tab3:
                    # Form to add new measurements
                    st.subheader("Add New Measurement")
                    
                    # Sensor selection dropdown
                    sensor_options = {f"{s.get('sensor_type')} at {s.get('position')} (ID: {s.get('sensor_id')})": s.get('sensor_id') for s in sensors}
                    selected_sensor_name = st.selectbox("Select Sensor", list(sensor_options.keys()))
                    selected_sensor_id = sensor_options[selected_sensor_name]
                    
                    # Value input
                    value = st.number_input("Measurement Value", min_value=0.0, value=20.0, step=0.1)
                    
                    # Submit button
                    if st.button("Add Measurement"):
                        success = add_measurement(selected_sensor_id, value)
                        if success:
                            st.success(f"Measurement added successfully for sensor {selected_sensor_id}!")
                            # Refresh data after 1 second
                            time.sleep(1)
                            st.rerun()