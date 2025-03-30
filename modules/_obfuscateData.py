import hashlib
from datetime import datetime, timezone

def obfuscate_data(properties, wifi_data_list, cellular_data_list, logger, loggerSetup):
    logger.log_message(loggerSetup, "START", "Obfuscating the WiFi & Cellular occupancy list")

    # Generate a key using the obfuscate secret
    obfuscate_secret = properties.get("obfuscate_secret", "")
    def obfuscate_field(value):
        key = f"{value}-{obfuscate_secret}"
        return hashlib.sha256(key.encode()).hexdigest()
    
    # Get raspberrypi serial number
    def getserial():
        cpuserial = "0000000000000000"
        try:
          f = open('/proc/cpuinfo','r')
          for line in f:
            if line[0:6]=='Serial':
              cpuserial = line[10:26]
          f.close()
        except:
          cpuserial = "ERROR000000000"
        
        return cpuserial

    # Extract and obfuscate the each field from data
    wifi_obfuscating_field = "DeviceMac"
    cellular_obfuscating_field = "TMSI"
    wifi_obfuscated_list = [
        obfuscate_field(item[wifi_obfuscating_field]) for item in wifi_data_list if wifi_obfuscating_field in item
    ]
    cellular_obfuscated_list = [
        obfuscate_field(item[cellular_obfuscating_field]) for item in cellular_data_list if cellular_obfuscating_field in item
    ]

    logger.log_message(loggerSetup, "INFO", f"Obfuscated WiFi:{len(wifi_obfuscated_list)} and Cellular:{len(cellular_obfuscated_list)} items.")

    # Get the current timestamp in ISO 8601 format
    current_utc_time = datetime.now(timezone.utc).isoformat()
    current_local_time = datetime.now().isoformat()

    # Create the final JSON object
    obfuscated_data = {
        "location-id": properties["location_id"],
        "device_id": f"{properties["device_id"]}-pi-{getserial()}",
        "utc_timestamp": current_utc_time,
        "local_timestamp": current_local_time,
        "wifi-occupancy-list": wifi_obfuscated_list,
        "cellular-occupancy-list": cellular_obfuscated_list
    }
    logger.log_message(loggerSetup, "INFO", "Occupancy data is ready to be sent!")
    return obfuscated_data
