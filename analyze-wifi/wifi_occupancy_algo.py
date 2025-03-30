import json
import time
import requests
import numpy as np
import os
import subprocess

# Function to get the WiFi occupancy counts
def get_wifi_occupancy_list(logger, properties, system_properties):
    # setting up logger
    log_prefix = "wifi-occupancy-algo"
    loggerSetup = logger.setup_logger(log_prefix)
    logger.log_message(loggerSetup, "INFO", "")
    logger.log_message(loggerSetup, "START", "Starting the WiFi Occupancy Algorithm")
    logger.enable_requests_logging(loggerSetup)

    module_status_code = 1

    # Starting Kismet Server usig bash and wait for next cloud sync
    manage_kismet_server("start", logger, loggerSetup)
    waiting_time = system_properties['cloud_sync_interval'] - 10
    logger.log_message(loggerSetup, "INFO", f"Waiting for {waiting_time} seconds for next cloud sync...")
    time.sleep(waiting_time)

    # Get device list active in past X seconds from Kismet API
    API_URL = f"http://{properties['kismet_server_username']}:{properties['kismet_server_password']}@{properties['kismet_server_ip']}:2501/devices/last-time/-{properties['last_seen_time_threshold']}/devices.prettyjson"

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
        logger.log_message(loggerSetup, "INFO", f"Fetching active devices list in last {properties['last_seen_time_threshold']} seconds from Kismet API")
        response = requests.post(API_URL, headers=REQUEST_HEADERS, json=REQUEST_BODY)
        if response.status_code != 200:
            logger.log_message(loggerSetup, "ERROR", f"Failed to fetch data: {response.status_code} {response.text}")
            logger.log_message(loggerSetup, "END", "Execution of WiFi algorithm failed")
            manage_kismet_server("stop", logger, loggerSetup)
            return [], module_status_code
        kismet_recentActive_response = response.json()
        logger.log_message(loggerSetup, "INFO", f"Received {len(kismet_recentActive_response)} devices from Kismet API")
    except Exception as e:
        logger.log_message(loggerSetup, "ERROR", f"An error occurred while fetching data from Kismet API: {str(e)}")
        logger.log_message(loggerSetup, "END", "Execution of WiFi algorithm failed")
        manage_kismet_server("stop", logger, loggerSetup)
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
    ##--- Debug: Save raw data to file
    logger.log_message(loggerSetup, "DEBUG", "Saving AP removed data to debug_ap-filtered-list.json")
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
        non_zero_signal_strength_array = [x for x in signal_strengths_array if x != 0] # remove zero signal levels
        if not non_zero_signal_strength_array: # skip if all signal levels are zero
            continue
        median_signal_level = np.median(non_zero_signal_strength_array)  # median signal level seen in last 60 seconds 
        deviation_list_from_median = [(current_level - (median_signal_level - properties['max_deviation'])) for current_level in non_zero_signal_strength_array if current_level != 0] # deviation of each signal level from median (positive means good signal, negative means bad signal)
        # count of signal levels which are out of range (means bad signal)
        no_of_out_of_range_count = sum(1 for each_deviation in deviation_list_from_median if each_deviation < 0)    
        
        # count of signal levels which are out of range
        if frequency_band < 15:     # 2.4GHz band use channel 1-14
            if median_signal_level >= properties['signal_threshold_24GHz'] and no_of_out_of_range_count <= round(len(non_zero_signal_strength_array) * properties['max_deviation_percentage']):
                recentActive_nearby_list.append(device)
        elif frequency_band >= 15:  # 5GHz band use channel 15-165
            if median_signal_level >= properties['signal_threshold_5GHz'] and no_of_out_of_range_count <= round(len(non_zero_signal_strength_array) * properties['max_deviation_percentage']):
                recentActive_nearby_list.append(device)
    logger.log_message(loggerSetup, "INFO", f"Filtered {len(recentActive_nearby_list)} devices as near by based on signal strength")


    # Step 4: Return filtered list
    ##--- Debug: Save filtered data to file
    logger.log_message(loggerSetup, "DEBUG", f"Saving filtered data to recentActive_nearby_list.json")
    # output_file = "recentActive_nearby_list.json"
    # with open(output_file, "w") as file:
    #     json.dump(recentActive_nearby_list, file, indent=4)
    # logger.log_message(loggerSetup, "DEBUG", f"Filtered data saved to {output_file}")

    logger.log_message(loggerSetup, "INFO", "Returning the filtered list of devices")
    module_status_code = 0
    manage_kismet_server("stop", logger, loggerSetup)
    logger.log_message(loggerSetup, "END", "Executed the WiFi algorithm")
    return recentActive_nearby_list, module_status_code


# Function to manage Kismet server
# This function starts and stops the Kismet server, and removes Kismet files if needed
def manage_kismet_server(action, logger, loggerSetup):
    PID_FILE = "/tmp/kismet_scan.pid"

    if action == "start":
        if os.path.exists(PID_FILE):
            logger.log_message(loggerSetup, "WARNING", f"Kismet server is already running with PID {open(PID_FILE).read().strip()}. Trying to stop it...")
            try:
                with open(PID_FILE, "r") as pid_file:
                    pid = int(pid_file.read().strip())
                os.kill(pid, 9)
                os.remove(PID_FILE)
                logger.log_message(loggerSetup, "INFO", f"Kismet server with PID {pid} stopped.")
            except Exception as e:
                logger.log_message(loggerSetup, "WARNING", f"No previous Kismet server to stop with PID: {str(e)}")
        try:
            logger.log_message(loggerSetup, "INFO", "Starting Kismet server...")
            command = ["kismet", "--override", "pol"]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            with open(PID_FILE, "w") as pid_file:
                pid_file.write(str(process.pid))
            logger.log_message(loggerSetup, "INFO", f"Kismet server started with PID {process.pid}.")
        except Exception as e:
            logger.log_message(loggerSetup, "ERROR", f"Failed to start Kismet server: {str(e)}")

    elif action == "stop":
        if not os.path.exists(PID_FILE):
            logger.log_message(loggerSetup, "ERROR", "No running Kismet server found.")
            return
        try:
            with open(PID_FILE, "r") as pid_file:
                pid = int(pid_file.read().strip())
            logger.log_message(loggerSetup, "INFO", f"Stopping Kismet server with PID {pid}...")
            os.kill(pid, 9)
            os.remove(PID_FILE)
            logger.log_message(loggerSetup, "INFO", "Kismet server stopped.")

            # Remove Kismet files ending with .kismet and .kismet-* in the current directory
            for filename in os.listdir("."):
                if filename.endswith(".kismet") or filename.endswith("kismet-journal"):
                    os.remove(filename)
                    logger.log_message(loggerSetup, "DEBUG", f"Removed Kismet file: {filename}")
            logger.log_message(loggerSetup, "INFO", "Removed Kismet files.")

        except Exception as e:
            logger.log_message(loggerSetup, "ERROR", f"Failed to stop Kismet server: {str(e)}")
