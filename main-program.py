import json
import sys
import os
import concurrent.futures

# Dynamically add the modules directory to sys.path
modules_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules")
if modules_path not in sys.path:
    sys.path.append(modules_path)
# Dynamically add the analyze-wifi directory to sys.path
analyze_wifi_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analyze-wifi")
if analyze_wifi_path not in sys.path:
    sys.path.append(analyze_wifi_path)
# Dynamically add the analyze-cellular directory to sys.path
analyze_cellular_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analyze-cellular")
if analyze_cellular_path not in sys.path:
    sys.path.append(analyze_cellular_path)
# Custom modules
import _logger as logger
import _readProperties as readProperties
import _checkModules as checkModules
import _obfuscateData as obfuscateData
import wifi_occupancy_algo as wifiOccupancy
import cellular_occupancy_algo as cellularOccupancy


################# Execution starts here #################
# setting up logger
log_prefix = "main-program"
log_module = "Main"
loggerSetup = logger.setup_logger(log_prefix, log_module)
logger.log_message(loggerSetup, "INFO", "")
logger.log_message(loggerSetup, "INFO", "###################   Starting the Main Program   ###################")

try:
    # reading properties
    logger.log_message(loggerSetup, "INFO", f"Loading properties...")
    system_properties = readProperties.system_properties(loggerSetup)
    wifi_properties = readProperties.wifi_properties(loggerSetup)
    cellular_properties = readProperties.cellular_properties(loggerSetup)

    # Check if the required modules are available
    logger.log_message(loggerSetup, "INFO", "Checking the devices...")
    module_status_code = checkModules.check_devices(logger, loggerSetup)
    if module_status_code != 0:
        sys.exit(1)
    else:
        logger.log_message(loggerSetup, "INFO", "All devices are available!")

    # Run WiFi and Cellular occupancy list retrieval in parallel
    logger.log_message(loggerSetup, "INFO", "Getting the WiFi and Cellular occupancy lists in parallel...")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        wifi_future = executor.submit(wifiOccupancy.get_wifi_occupancy_list, logger, wifi_properties, system_properties)
        cellular_future = executor.submit(cellularOccupancy.get_cellular_occupancy_list, logger, cellular_properties, system_properties)

        # Wait for both tasks to complete
        wifi_occupancy_list, wifi_status_code = wifi_future.result()
        cellular_occupancy_list, cellular_status_code = cellular_future.result()

    # Check results of WiFi occupancy list retrieval
    if wifi_status_code != 0:
        logger.log_message(loggerSetup, "ERROR", "Error occurred while getting the WiFi occupancy list.")
        sys.exit(1)
    else:
        logger.log_message(loggerSetup, "INFO", "WiFi occupancy list obtained successfully!")

    # Check results of Cellular occupancy list retrieval
    if cellular_status_code != 0:
        logger.log_message(loggerSetup, "ERROR", "Error occurred while getting the Cellular occupancy list.")
        sys.exit(1)
    else:
        logger.log_message(loggerSetup, "INFO", "Cellular occupancy list obtained successfully!")

    # Obfuscate the data
    obfuscated_data = obfuscateData.obfuscate_data(system_properties, wifi_occupancy_list, cellular_occupancy_list, logger, loggerSetup)
    
    ##--- Debug: Save the obfuscated data to a file
    with open("obfuscated-data.json", "w") as file:
        json.dump(obfuscated_data, file, indent=4)
    logger.log_message(loggerSetup, "DEBUG", "Obfuscated data saved to 'obfuscated-data.json' file.")


    logger.log_message(loggerSetup, "INFO", "###################   Ended the Main Program   ###################")
except Exception as e:
    logger.log_message(loggerSetup, "ERROR", f"An error occurred: {str(e)}")
