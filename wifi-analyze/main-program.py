import json
import sys
import os
# Dynamically add the modules directory to sys.path
modules_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules")
if modules_path not in sys.path:
    sys.path.append(modules_path)
# Custom modules
import __logger as logger
import __readProperties as readProperties
import __obfuscateData as obfuscateData
import _wifi_occupancy_algo as wifiOccupancy


################# Execution starts here #################
# setting up logger
log_prefix = "main-program"
loggerSetup = logger.setup_logger(log_prefix)
logger.log_message(loggerSetup, "INFO", "")
logger.log_message(loggerSetup, "INFO", "###################   Starting the Main Program   ###################")

try:
    properties = readProperties.load_properties(loggerSetup, "system")
    location_id = properties["location_id"]
    device_id = properties["device_id"]

    # Get the WiFi occupancy list
    logger.log_message(loggerSetup, "INFO", "Getting the WiFi occupancy list...")
    wifi_occupancy_list, module_status_code = wifiOccupancy.get_wifi_occupancy_list()
    if module_status_code != 0:
        logger.log_message(loggerSetup, "ERROR", "Error occurred while getting the WiFi occupancy list.")
        sys.exit(1)
    else:
        logger.log_message(loggerSetup, "INFO", "WiFi occupancy list obtained successfully!")
    # Obfuscate the wifi data
    obfuscated_data = obfuscateData.obfuscated_wifi_data(location_id, device_id, wifi_occupancy_list, "DeviceMac", loggerSetup)
    # Save the obfuscated data to a file
    with open("obfuscated-wifi-data.json", "w") as file:
        json.dump(obfuscated_data, file, indent=4)
    logger.log_message(loggerSetup, "DEBUG", "Obfuscated data saved to 'obfuscated-wifi-data.json' file.")




    logger.log_message(loggerSetup, "INFO", "###################   Ended the Main Program   ###################")
except Exception as e:
    logger.log_message(loggerSetup, "ERROR", f"An error occurred: {str(e)}")
