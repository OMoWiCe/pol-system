# How the Cellular Occupancy ALO algorithm works

# Read nearby_channels.json file
# If file not found or empty, run cell_scan function
    # cell_scan function: scan each given band and store channel, its frequency in a list
        # command: grgsm_scanner -b GSM900 -s 1600000.0 --speed=5 -v
        # command: grgsm_scanner -b DCS1800 -s 1600000.0 --speed=5 -v
    # then save the list to nearby_channels.json file
    # once done re execute this python program
# If file is not empty, read the file and add the data to a list
# channels = [{
#     "arfcn": 0,
#     "band": "GSM900",
#     "frequency": 935.0}]

# calculate cell_timer by dividing cloud_sync_interval by number of channels and minus 1sec
# Loop through the channels
    # if the channel is not empty, run the channel_capture function
    # start cell_timer
    # Run packet_capture function and decode_packets functions parallelly
        # packet_capture command: grgsm_livemon_headless -f 936.6M -s 1.4M
        # decode_packets command: sudo tshark -i lo -Y "e212.imsi" -V (And then need to filter the output to get below details)
    # Add decoded packets details which has TMSI to a list (May has multiple TMSI, add all to the list)
        # mobile_stations = [
#               { tmsi: "0x120ff0d7",
#                 arfcn: "7",
#                 signal_level: "-65"}
#               ]
    # stop packet_capture and decode_packets functions when cell_timer is up
# if no more channels, get the unique IMSI from the list
# return the unique IMSI list

## Let's code now :D

import os
import json
import time
import subprocess

# Function to read the channel data from nearby_channels.json file
def read_channel_file(file_path, logger):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                data = json.load(file)
                logger.log_message(logger, "INFO", f"Read {len(data)} channels from {file_path}")
                return data
        else:
            logger.log_message(logger, "ERROR", f"File {file_path} not found. Running cell_scan...")
            return None
    except Exception as e:
        logger.log_message(logger, "ERROR", f"Error reading channel file: {e}")
        return None

# Function to write the channel data to nearby_channels.json file
def write_channel_file(file_path, data, logger):
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
            logger.log_message(logger, "INFO", f"Wrote {len(data)} channels to {file_path}")
    except Exception as e:
        logger.log_message(logger, "ERROR", f"Error writing channel file: {e}")

# Function to scan the channels using grgsm_scanner
def cell_scan(bands, sample_rate, logger):
    try:
        logger.log_message(logger, "INFO", f"Starting Scanning bands: {bands} with sample rate: {sample_rate}")
        channels = []
        for band in bands:
            command = f"grgsm_scanner -b {band} -s {sample_rate} --speed=5"
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                logger.log_message(logger, "ERROR", f"Error running command: {command}")
                continue
            for line in result.stdout.splitlines():
                if "ARFCN" in line:
                    parts = line.split(",")
                    arfcn = parts[0].split(":")[1].strip()
                    frequency = parts[1].split(":")[1].strip()
                    power = parts[6].split(":")[1].strip()
                    channels.append({"arfcn": arfcn, "frequency": frequency, "power": power, "band": band})
                    logger.log_message(logger, "DEBUG", f"Found channel: {arfcn}, frequency: {frequency}, power: {power}, band: {band}")
        logger.log_message(logger, "INFO", f"Found {len(channels)} channels in total")
        return channels
    except Exception as e:
        logger.log_message(logger, "ERROR", f"Error during cell scan: {e}")
        return []

# Function to capture packets using grgsm_livemon_headless
def channel_capture(frequency, sample_rate, logger):
    logger.log_message(logger, "DEBUG", f"Starting channel capture on frequency: {frequency} with sample rate: {sample_rate}")
    command = f"grgsm_livemon_headless -f {frequency}M -s {sample_rate}"
    process = subprocess.Popen(command, shell=True)
    return process

# Function to decode packets using tshark
def decode_packets(logger):
    logger.log_message(logger, "DEBUG", "Starting packet decoding with tshark")
    command = "sudo tshark -i lo -Y 'e212.imsi' -V"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process

# Function to filter the decoded packets and get the required details
def filter_packets(output, logger):
    logger.log_message(logger, "DEBUG", "Filtering packets for TMSI")
    mobile_stations = []
    lines = output.splitlines()
    for line in lines:
        if "TMSI" in line:
            parts = line.split()
            tmsi = parts[1]
            arfcn = parts[3]
            signal_level = parts[5]
            mobile_stations.append({"tmsi": tmsi, "arfcn": arfcn, "signal_level": signal_level})
            logger.log_message(logger, "DEBUG", f"Found mobile station: TMSI: {tmsi}, ARFCN: {arfcn}, Signal Level: {signal_level}")
    logger.log_message(logger, "DEBUG", f"Filtered {len(mobile_stations)} mobile stations")
    return mobile_stations

# Function to run the packet capture and decoding in parallel
def run_capture_and_decode(frequency, sample_rate, cell_timer, logger):
    try:
        capture_process = channel_capture(frequency, sample_rate, logger)
        decode_process = decode_packets(logger)
        time.sleep(cell_timer)
        capture_process.terminate()
        decode_process.terminate()
        logger.log_message(logger, "DEBUG", f"Terminated capture and decode processes after {cell_timer} seconds for frequency: {frequency}")
        return capture_process, decode_process
    except Exception as e:
        logger.log_message(logger, "ERROR", f"Error during capture and decode: {e}")
        return None, None

# Function to get unique TMSI from the mobile stations list
def get_unique_tmsi(mobile_stations, logger):
    unique_tmsi = set()
    for station in mobile_stations:
        unique_tmsi.add(station["tmsi"])
    logger.log_message(logger, "INFO", f"Found {len(unique_tmsi)} unique TMSI")
    return list(unique_tmsi)


################ Main function to run the Cellular Occupancy ALO algorithm
def get_cellular_occupancy_list(logger, cellular_properties, system_properties):
    try:
        # setting up logger
        log_prefix = "cellular-occupancy-algo"
        loggerSetup = logger.setup_logger(log_prefix)
        logger.log_message(loggerSetup, "INFO", "")
        logger.log_message(loggerSetup, "START", "Starting the Cellular Occupancy Algorithm")
        logger.enable_requests_logging(loggerSetup)

        module_status_code = 1

        # Defining the variables
        channel_list_file_path = "nearby_channels.json"
        bands = cellular_properties["cellular_band"]
        sample_rate = cellular_properties["sdr_sample_rate"]
        signal_threshold = cellular_properties["signal_threshold"]
        cell_timer = 0
        mobile_stations = []

        # Read the channel data from the file
        channels = read_channel_file(channel_list_file_path, logger)
        # If the file is empty or not found, run the cell_scan function
        if not channels:
            channels = cell_scan(bands, sample_rate, logger)
            write_channel_file(channel_list_file_path, channels, logger)
            logger.log_message(loggerSetup, "INFO", f"Restart the Cellular Occupancy Algorithem to use the scanned channels.")
            return [], module_status_code

        # Calculate cell_timer
        cell_timer = (system_properties["cloud_sync_interval"] / len(channels)) - 1
        logger.log_message(loggerSetup, "INFO", f"Calculated cell timer: {cell_timer} seconds")

        # Loop through the channels and capture packets
        logger.log_message(loggerSetup, "INFO", f"Starting packet capture on {len(channels)} channels...")
        for channel in channels:
            frequency = channel["frequency"]
            capture_process, decode_process = run_capture_and_decode(frequency, sample_rate, cell_timer, logger)
            if not capture_process or not decode_process:
                continue
            # Get the output from the decode process
            output, _ = decode_process.communicate()
            # Filter the packets and get the mobile stations
            filtered_stations = filter_packets(output, logger)
            mobile_stations.extend(filtered_stations)
        logger.log_message(loggerSetup, "INFO", f"Captured {len(mobile_stations)} mobile stations in total")

        # Get unique TMSI from the mobile stations list
        logger.log_message(loggerSetup, "INFO", f"Getting unique TMSI from the mobile stations list...")
        unique_ms = get_unique_tmsi(mobile_stations, logger)

        module_status_code = 0
        return unique_ms, module_status_code
    except Exception as e:
        return [], module_status_code