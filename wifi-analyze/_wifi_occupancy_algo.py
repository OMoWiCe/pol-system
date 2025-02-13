import json
import requests
import numpy as np
import sys
import os
# Dynamically add the modules directory to sys.path
modules_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules")
if modules_path not in sys.path:
    sys.path.append(modules_path)
# Custom modules
import __logger as logger # type: ignore
import __readProperties as readProperties # type: ignore


# Function to get the WiFi occupancy counts
def get_wifi_occupancy_list():
    """
    Get latest nearby Wifi devices based on signal strength
    Returns:
        list: List of devices with thier details which are nearby based on signal strength.
    """
    # setting up logger
    log_prefix = "wifi-occupancy-algo"
    loggerSetup = logger.setup_logger(log_prefix)
    logger.log_message(loggerSetup, "INFO", "")
    logger.log_message(loggerSetup, "START", "Starting the WiFi Occupancy Algorithm")
    logger.enable_requests_logging(loggerSetup)
    # Read properties
    properties = readProperties.load_properties(loggerSetup, "wifi-occupancy algorithm")
    try:
        last_seen_time_threshold = int(properties["last_seen_time_threshold"])
        out_of_range_signal_level = int(properties["out_of_range_signal_level"])
        max_out_of_range_repeat_count = int(properties["max_out_of_range_repeat_count"])
        signal_threshold_24GHz = int(properties["signal_threshold_24ghz"])
        signal_threshold_5GHz = int(properties["signal_threshold_5ghz"])
        kismet_server_ip = properties["kismet_server_ip"]
        kismet_server_username = properties["kismet_username"]
        kismet_server_password = properties["kismet_password"]
    except Exception as e:
        last_seen_time_threshold=300
        out_of_range_signal_level=-72
        max_out_of_range_repeat_count=10
        signal_threshold_24GHz=-60
        signal_threshold_5GHz=-67
        kismet_server_ip="localhost"
    module_status_code = 1

    # Get device list active in past X seconds from Kismet API
    API_URL = f"http://{kismet_server_username}:{kismet_server_password}@{kismet_server_ip}:2501/devices/last-time/-{last_seen_time_threshold}/devices.prettyjson"
    REQUEST_HEADERS = {"Content-Type": "application/json"}
    REQUEST_BODY = {
         "fields":[
        "kismet.device.base.type",
        "kismet.device.base.macaddr",
        "kismet.device.base.signal/kismet.common.signal.signal_rrd/kismet.common.rrd.minute_vec",
        "dot11.device/dot11.device.last_bssid",
        "kismet.device.base.mod_time",
        "kismet.device.base.channel"
    ]}

    # Step 1: Fetch data from Kismet API
    try:
        logger.log_message(loggerSetup, "INFO", f"Fetching active devices list in last {last_seen_time_threshold} seconds from Kismet API")
        response = requests.post(API_URL, headers=REQUEST_HEADERS, json=REQUEST_BODY)
        if response.status_code != 200:
            logger.log_message(loggerSetup, "ERROR", f"Failed to fetch data: {response.status_code} {response.text}")
            logger.log_message(loggerSetup, "END", "Execution of WiFi algorithm failed")
            return [], module_status_code
        kismet_recentActive_response = response.json()
        logger.log_message(loggerSetup, "INFO", f"Received {len(kismet_recentActive_response)} devices from Kismet API")
    except Exception as e:
        logger.log_message(loggerSetup, "ERROR", f"An error occurred while fetching data from Kismet API: {str(e)}")
        logger.log_message(loggerSetup, "END", "Execution of WiFi algorithm failed")
        return [], module_status_code


    # Step 2: Remove APs from the list and extract required fields
    ap_removed_recentActive_list = []
    for device in kismet_recentActive_response:
        if device.get("kismet.device.base.type") != "Wi-Fi AP":
            ap_removed_recentActive_list.append({
                "DeviceType": device.get("kismet.device.base.type"),
                "DeviceMac": device.get("kismet.device.base.macaddr"),
                "SignalStrengthArray": device.get("kismet.common.rrd.minute_vec", []),
                "ConnectedBSSID": device.get("dot11.device.last_bssid"),
                "LastSeenTime": device.get("kismet.device.base.mod_time"),
                "WorkingFrequnceyBand": int(device.get("kismet.device.base.channel") or 0),
            })
    logger.log_message(loggerSetup, "INFO", f"Removed {len(kismet_recentActive_response) - len(ap_removed_recentActive_list)} APs from the list")
    ###--- Debug: Save raw data to file
    # logger.log_message(loggerSetup, "DEBUG", "Saving AP removed data to debug_ap-filtered-list.json")
    # with open("debug_ap-filtered-list.json", "w") as file:
    #     json.dump(ap_removed_recentActive_list, file, indent=4)


    # Step 3: Apply filtering based on signal strength and frequency
    recentActive_nearby_list = []
    for device in ap_removed_recentActive_list:
        frequency_band = device["WorkingFrequnceyBand"]
        signal_strengths_array = device["SignalStrengthArray"]

        # Skip if signal_strengths_array or frequency_band is empty
        if not signal_strengths_array or not frequency_band:
            continue

        # calculate values for the filtering
        median_signal_level = np.median(signal_strengths_array)   # median signal level seen in last 60 seconds
        deviation_list_from_median = [abs(current_level - median_signal_level) for current_level in signal_strengths_array if current_level != 0]   
        # determine deviation of each signal level from median
        no_of_out_of_range_count = sum(1 for each_deviation in deviation_list_from_median if each_deviation < out_of_range_signal_level)    
        
        # count of signal levels which are out of range
        if frequency_band < 15:     # 2.4GHz band
            if median_signal_level >= signal_threshold_24GHz and no_of_out_of_range_count < max_out_of_range_repeat_count:
                recentActive_nearby_list.append(device)
        elif frequency_band >= 15:  # 5GHz band
            if median_signal_level >= signal_threshold_5GHz and no_of_out_of_range_count < max_out_of_range_repeat_count:
                recentActive_nearby_list.append(device)
    logger.log_message(loggerSetup, "INFO", f"Filtered {len(recentActive_nearby_list)} devices as near by based on signal strength")


    # Step 4: Save filtered list to file
    # logger.log_message(loggerSetup, "DEBUG", f"Saving filtered data to recentActive_nearby_list.json")
    # output_file = "recentActive_nearby_list.json"
    # with open(output_file, "w") as file:
    #     json.dump(recentActive_nearby_list, file, indent=4)
    # logger.log_message(loggerSetup, "DEBUG", f"Filtered data saved to {output_file}")
    logger.log_message(loggerSetup, "INFO", "Returning the filtered list of devices")
    module_status_code = 0
    logger.log_message(loggerSetup, "END", "Executed the WiFi algorithm")

    return recentActive_nearby_list, module_status_code
