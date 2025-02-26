import streamlit as st
import pandas as pd
import numpy as np

# App title
st.title("🥊 Rock Steady Boxing Dashboard")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Live Feedback", "Settings"])

# Simulating sensor data fetching from RDS (for now, using random data)
def get_sensor_data(sensor_name):
    #Simulate fetching sensor data from the database

    time_series = np.arange(1, 11)  # Example time points
    values = np.random.randint(10, 50, size=10)  # Example sensor values
    return pd.DataFrame({"Time": time_series, "Value": values})

# Home Page
if page == "Home":
    st.header("Welcome to the Rock Steady Sensor Dashboard")
    st.write("This is a simple Streamlit app to visualize sensor data.")

# Live Sensor Data Page
elif page == "Live Feedback":

    
    if "selected_sensor" not in st.session_state:
        st.header("📈 Live Sensor Data")
        # Example list of sensors
        sensors = ["Sensor A", "Sensor B", "Sensor C", "Sensor D", "Sensor E", "Sensor F"]
    
        # Layout: 3 sensors per row
        cols = st.columns(3)
        for i, sensor in enumerate(sensors):
            with cols[i % 3]:  # distribute in 3-column layout
                st.subheader(sensor)
                df = get_sensor_data(sensor)
                st.line_chart(df.set_index("Time"))
                if st.button(f"More about {sensor}", key=sensor):
                    st.session_state["selected_sensor"] = sensor
                    st.rerun()  # Navigate to detailed sensor view

# Sensor Detail Page
if "selected_sensor" in st.session_state:
    selected_sensor = st.session_state["selected_sensor"]
    st.header(f"📊 Sensor Details: {selected_sensor}")
    st.write(f"Showing detailed data for {selected_sensor}.")
    df = get_sensor_data(selected_sensor)
    st.line_chart(df.set_index("Time"))

    if st.button("Back to Live Feedback"):
        del st.session_state["selected_sensor"]
        st.rerun()

# Settings Page
elif page == "Settings":
    st.header("⚙️ Settings")
    st.write("Modify your preferences here.")
