import json
import sys
import os

# Dynamically add the modules directory to sys.path
modules_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules")
if modules_path not in sys.path:
    sys.path.append(modules_path)
# Dynamically add the analyze-wifi directory to sys.path
analyze_wifi_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analyze-wifi")
if analyze_wifi_path not in sys.path:
    sys.path.append(analyze_wifi_path)
# Custom modules
import _logger as logger
import _readProperties as readProperties
import _obfuscateData as obfuscateData
import wifi_occupancy_algo as wifiOccupancy


################# Execution starts here #################
# setting up logger
log_prefix = "main-program"
loggerSetup = logger.setup_logger(log_prefix)
logger.log_message(loggerSetup, "INFO", "")
logger.log_message(loggerSetup, "INFO", "###################   Starting the Main Program   ###################")

try:
    # reading properties
    system_properties = readProperties.system_properties(loggerSetup)
    wifi_properties = readProperties.wifi_properties(loggerSetup)

    # Get the WiFi occupancy list
    logger.log_message(loggerSetup, "INFO", "Getting the WiFi occupancy list...")
    wifi_occupancy_list, module_status_code = wifiOccupancy.get_wifi_occupancy_list(logger, wifi_properties)
    if module_status_code != 0:
        logger.log_message(loggerSetup, "ERROR", "Error occurred while getting the WiFi occupancy list.")
        sys.exit(1)
    else:
        logger.log_message(loggerSetup, "INFO", "WiFi occupancy list obtained successfully!")



    
    # Obfuscate the wifi data
    obfuscated_data = obfuscateData.obfuscated_wifi_data(system_properties["location_id"], system_properties["device_id"], wifi_occupancy_list, "DeviceMac",logger, loggerSetup)
    # Save the obfuscated data to a file
    with open("obfuscated-wifi-data.json", "w") as file:
        json.dump(obfuscated_data, file, indent=4)
    logger.log_message(loggerSetup, "DEBUG", "Obfuscated data saved to 'obfuscated-wifi-data.json' file.")


    logger.log_message(loggerSetup, "INFO", "###################   Ended the Main Program   ###################")
except Exception as e:
    logger.log_message(loggerSetup, "ERROR", f"An error occurred: {str(e)}")
