import os
from configparser import ConfigParser
import _logger as logger

# Default properties file name
file_name="system.properties"

# Function to load properties from a file
def load_properties(loggerSetup, module:str):
    """
    Loads properties from a file and returns them as a dictionary.
    Args:
        file_name (str): Name of the properties file (default: system.properties).
    Returns:
        dict: Dictionary of properties and their values.
    """
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Define the path to the properties file (located one directory before)
    properties_file_path = os.path.join(project_root, file_name)

    # Check if the file exists
    if not os.path.exists(properties_file_path):
        logger.log_message(loggerSetup, "WARNING", f"{file_name} not found in the project directory. Using default values!")
    else:
        # Parse the properties file
        config = ConfigParser()
        config.read(properties_file_path)
        logger.log_message(loggerSetup, "INFO", f"{module} properties loaded successfully!")
        # Extract values and return as a dictionary
        return {key: eval(value) for key, value in config["DEFAULT"].items()}

# Function to load System properties
def system_properties(loggerSetup):
    properties = load_properties(loggerSetup, "system")
    try:
        location_id = properties["location_id"]
        device_id = properties["device_id"]
        cloud_sync_interval = int(properties["cloud_sync_interval"])
        obfuscate_secret = properties["obfuscate_secret"]
    except Exception as e:
        location_id = "default"
        device_id = "default"
        cloud_sync_interval = 300
        obfuscate_secret = "default"
    # return properties with key value pairs
    return {"location_id": location_id, "device_id": device_id, "cloud_sync_interval": cloud_sync_interval, "obfuscate_secret": obfuscate_secret}


# Function to load WiFi properties
def wifi_properties(loggerSetup):
    properties = load_properties(loggerSetup, "wifi-occupancy-algo")
    try: 
        kismet_server_ip = properties["kismet_server_ip"]
        kismet_server_username = properties["kismet_username"]
        kismet_server_password = properties["kismet_password"]
        last_seen_time_threshold = int(properties["last_seen_time_threshold"])
        signal_threshold_24GHz = int(properties["signal_threshold_24ghz"])
        signal_threshold_5GHz = int(properties["signal_threshold_5ghz"])
        max_deviation = int(properties["max_deviation"])
        max_deviation_percentage = float(properties["max_deviation_percentage"])/100

    except Exception as e:
        kismet_server_ip="localhost"
        last_seen_time_threshold=300
        signal_threshold_24GHz=-60
        signal_threshold_5GHz=-67
        max_deviation=10
        max_deviation_percentage=50
        
    # return properties with key value pairs
    return {"last_seen_time_threshold": last_seen_time_threshold, "max_deviation": max_deviation, "max_deviation_percentage": max_deviation_percentage, "signal_threshold_24GHz": signal_threshold_24GHz, "signal_threshold_5GHz": signal_threshold_5GHz, "kismet_server_ip": kismet_server_ip, "kismet_server_username": kismet_server_username, "kismet_server_password": kismet_server_password}

# Function to load Cellular properties
def cellular_properties(loggerSetup):
    properties = load_properties(loggerSetup, "cellular-occupancy-algo")
    try:
        sdr_sample_rate = float(properties["sdr_sample_rate"])
        cellular_mode = properties["cellular_mode"]
        if cellular_mode not in ["GSM", "UMTS", "LTE"]:
            raise ValueError("Invalid cellular mode. Must be 'GSM', 'UMTS', or 'LTE'.")
        cellular_band = [band.strip() for band in properties["cellular_band"].split(",")]
        signal_threshold = int(properties["signal_threshold"])
        cell_scan_expire_time = int(properties["cell_scan_expire_time"])
        if cell_scan_expire_time <= 0:
            raise ValueError("cell_scan_expire_time must be a positive integer.")
    except Exception as e:
        sdr_sample_rate = 1.6e6
        cellular_mode = "GSM"
        cellular_band = 'GSM900, DCS1800'
        signal_threshold = -30
        cell_scan_expire_time = 1800

    # return properties with key value pairs
    return {"sdr_sample_rate": sdr_sample_rate, "cellular_mode": cellular_mode, "cellular_band": cellular_band, "signal_threshold": signal_threshold, "cell_scan_expire_time": cell_scan_expire_time}