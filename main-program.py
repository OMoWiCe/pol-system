#!/root/research-work/pol-system/venv/bin/python
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
import _sendToAzure as sendToAzure
import wifi_occupancy_algo as wifiOccupancy
import cellular_occupancy_algo as cellularOccupancy


################# Execution starts here #################
# setting up logger
log_prefix = "main-program"
log_module = "Main"
loggerSetup = logger.setup_logger(log_prefix, log_module)
logger.log_message(loggerSetup, "INFO", "###################   Starting the Main Program   ###################")

try:
    # ####### LOCAL TESTING PURPOSES ONLY - START ######
    # iteration = 1  # Initialize iteration counter
    # test_capturing_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test-capturing")
    # os.makedirs(test_capturing_folder, exist_ok=True)  # Ensure the folder exists
    # ####### LOCAL TESTING PURPOSES ONLY - END ######

    # while True:  # Loop until interrupted
    #     logger.log_message(loggerSetup, "INFO", f"Starting iteration {iteration}...")

        ####### reading properties
        logger.log_message(loggerSetup, "INFO", f"Loading properties...")
        system_properties = readProperties.system_properties(loggerSetup)
        wifi_properties = readProperties.wifi_properties(loggerSetup)
        cellular_properties = readProperties.cellular_properties(loggerSetup)

        ####### Check if the required modules are available
        logger.log_message(loggerSetup, "INFO", "Checking the devices...")
        module_status_code = checkModules.check_devices(logger, loggerSetup)
        if module_status_code != 0:
            sys.exit(1)
        else:
            logger.log_message(loggerSetup, "INFO", "All devices are available!")

        ####### Run WiFi and Cellular occupancy list retrieval in parallel
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

        ####### Obfuscate the data
        obfuscated_data = obfuscateData.obfuscate_data(system_properties, wifi_occupancy_list, cellular_occupancy_list, logger, loggerSetup)
        
    #     ####### LOCAL TESTING PURPOSES ONLY - START ######
    #     ##--- Save the obfuscated data to a file with iteration number
    #     obfuscated_file_path = os.path.join(test_capturing_folder, f"obfuscated-data-{iteration}.json")
    #     with open(obfuscated_file_path, "w") as file:
    #         json.dump(obfuscated_data, file, indent=4)
    #     logger.log_message(loggerSetup, "DEBUG", f"Obfuscated data saved to '{obfuscated_file_path}'.")
    #     logger.log_message(loggerSetup, "INFO", f"Iteration {iteration} completed successfully.")
    #     logger.log_message(loggerSetup, "INFO", "------------------")
    #     iteration += 1  # Increment iteration counter
    #     ####### LOCAL TESTING PURPOSES ONLY - END ######

        ##--- Debug: Save the obfuscated data to a file
        with open("obfuscated-data.json", "w") as file:
            json.dump(obfuscated_data, file, indent=4)
        logger.log_message(loggerSetup, "DEBUG", "Obfuscated data saved to 'obfuscated-data.json' file.")

        ####### Sending the obfuscated data to the cloud
        logger.log_message(loggerSetup, "INFO", "Sending the obfuscated data to the cloud...")
        connection_string = system_properties["iot_hub_connection_string"]
        send_status_code = sendToAzure.send_to_iothub(obfuscated_data, connection_string, loggerSetup)
        if send_status_code != 0:
            sys.exit(1)
        else:
            logger.log_message(loggerSetup, "INFO", "Data sent to the cloud successfully!")

except KeyboardInterrupt:
    logger.log_message(loggerSetup, "WARNING", "Program interrupted by user. Exiting...")
except Exception as e:
    logger.log_message(loggerSetup, "ERROR", f"An error occurred: {str(e)}")
