# Streamlit Sensor Dashboard MVP

## Getting Started
This guide will walk you through setting up a virtual environment, installing dependencies, and running the MVP Streamlit app.

## Create a Virtual Environment
Before running the app, create and activate a virtual environment to manage dependencies.

### For Mac/Linux:
```
python -m venv venv
source venv/bin/activate
```

### For Windows:
```
python -m venv venv
venv\Scripts\activate
```

After activation, your terminal should show `(venv)` at the beginning of the line.

## Install Dependencies
With the virtual environment activated, install the required Python packages:
```
pip install -r requirements.txt
```

This ensures that all necessary dependencies are installed.

## Run the MVP Streamlit App
Once everything is set up, launch the app using:
```
streamlit run app.py
```

This will open the Streamlit dashboard in your web browser at:
```
http://localhost:8501
```

## Deactivating the Virtual Environment
When you're done working on the project, deactivate the virtual environment:
```
deactivate
```

For Windows PowerShell:
```
Deactivate
```

## Additional Notes
- Ensure you are using Python 3.8+ for compatibility.
- If you face issues installing dependencies, try upgrading `pip`:
  ```
  pip install --upgrade pip
  ```
- If needed, regenerate the `requirements.txt` file:
  ```
  pip freeze > requirements.txt
  ```

Happy coding!

