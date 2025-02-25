import streamlit as st

# App title
st.title("🥊 Rock Steady Boxing Dashboard")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Live Feedback", "Settings"])

# Home Page
if page == "Home":
    st.header("Welcome to the Rock Steady Sensor Dashboard")
    st.write("This is a simple Streamlit app to visualize sensor data.")

# Live Chart Page (Placeholder)
elif page == "Live Feedback":
    st.header("📈 Live Sensor Data")
    st.line_chart({"Time": [1, 2, 3, 4, 5], "Value": [10, 20, 15, 25, 30]})

# Settings Page (Placeholder)
elif page == "Settings":
    st.header("⚙️ Settings")
    st.write("Modify your preferences here.")