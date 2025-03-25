import hashlib
from datetime import datetime, timezone

def obfuscated_wifi_data(location_id, device_id, data_list, obfuscating_field, logger, loggerSetup):
    """
    Creates a JSON object with obfuscated MAC addresses or other specified field.
    Args:
        location_id (str): The location identifier.
        device_id (str): The device identifier.
        data_list (list): A list of dictionaries containing data to process.
        obfuscating_field (str): The field in the dictionaries to obfuscate.
    Returns:
        dict: JSON-like dictionary with obfuscated data.
    """
    logger.log_message(loggerSetup, "INFO", "Obfuscating the WiFi occupancy list...")
    # Function to obfuscate the passed field
    def obfuscate_field(value):
        return hashlib.sha256(value.encode()).hexdigest()
    
    # Extract and obfuscate the specified field from each item in the data list
    obfuscated_list = [
        obfuscate_field(item[obfuscating_field]) for item in data_list if obfuscating_field in item
    ]
    logger.log_message(loggerSetup, "INFO", f"Obfuscated {len(obfuscated_list)} items.")
    # Get the current timestamp in ISO 8601 format
    current_utc_time = datetime.now(timezone.utc).isoformat()
    current_local_time = datetime.now().isoformat()

    # Create the final JSON object
    obfuscated_data = {
        "location-id": location_id,
        "device_id": device_id,
        "utc_timestamp": current_utc_time,
        "local_timestamp": current_local_time,
        "occupancy-list": obfuscated_list
    }
    logger.log_message(loggerSetup, "INFO", "WiFi occupancy data is ready to be sent!")
    return obfuscated_data
