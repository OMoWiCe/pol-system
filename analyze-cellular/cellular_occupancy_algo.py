import os
import json
import time
import subprocess
import signal

# Function to handle termination signals for subprocesses
active_processes = []
def terminate_processes(signal_received, frame):
    global active_processes
    for process in active_processes:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except Exception as e:
            pass  # Ignore errors during termination
    exit(0)
# Register the signal handler
signal.signal(signal.SIGINT, terminate_processes)

# Function to read the channel data from nearby_channels.json file
def read_channel_file(file_path, cell_scan_expire_time, logger, loggerSetup):
    try:
        if os.path.exists(file_path):
            # Compare the file's modification time with the current time
            current_time = time.time()
            file_mod_time = os.path.getmtime(file_path)
            # If the file is older than cell_scan_expire_time, run cell_scan
            if current_time - file_mod_time > cell_scan_expire_time:
                logger.log_message(loggerSetup, "WARNING", f"File {file_path} is older than {cell_scan_expire_time} seconds. Running cell_scan...")
                return None
            # If the file is not older than cell_scan_expire_time, read the data
            with open(file_path, 'r') as file:
                data = json.load(file)
                logger.log_message(loggerSetup, "INFO", f"Read {len(data)} channels from {file_path}")
                return data
        else:
            logger.log_message(loggerSetup, "ERROR", f"File {file_path} not found. Running cell_scan...")
            return None
    except Exception as e:
        logger.log_message(loggerSetup, "ERROR", f"Error reading channel file: {e}")
        return None

# Function to write the channel data to nearby_channels.json file
def write_channel_file(file_path, data, logger, loggerSetup):
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)
            logger.log_message(loggerSetup, "DEBUG", f"Wrote {len(data)} channels to {file_path}")
    except Exception as e:
        logger.log_message(loggerSetup, "ERROR", f"Error writing channel file: {e}")

# Function to scan the channels using grgsm_scanner
def cell_scan(bands, sample_rate, logger, loggerSetup):
    try:
        logger.log_message(loggerSetup, "INFO", f"Starting Scanning bands: {bands} with sample rate: {sample_rate}")
        start_time = time.time()
        channels = []
        for band in bands:
            logger.log_message(loggerSetup, "DEBUG", f"Scanning band: {band}")
            command = f"grgsm_scanner -b {band} -s {sample_rate} --speed=5 --arg=hackrf"
            # handle the process group to allow for termination
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)  # Use os.setsid
            active_processes.append(process)  # Register the process
            result = process.communicate()  # Wait for the process to complete
            active_processes.remove(process)  # Remove the process after completion
            if process.returncode != 0:
                logger.log_message(loggerSetup, "ERROR", f"Error running command: {command}")
                continue
            for line in result[0].decode('utf-8').splitlines():
                if "ARFCN" in line:
                    parts = line.split(",")
                    arfcn = parts[0].split(":")[1].strip()
                    frequency = parts[1].split(":")[1].strip()
                    power = parts[6].split(":")[1].strip()
                    channels.append({"arfcn": arfcn, "frequency": frequency, "power": power, "band": band})
                    logger.log_message(loggerSetup, "DEBUG", f"Found channel: {arfcn}, frequency: {frequency}, power: {power}, band: {band}")
        logger.log_message(loggerSetup, "DEBUG", f"Found {len(channels)} channels in total")
        # getting the unique channels
        unique_channels = []
        unique_channels_list = []
        for channel in channels:
            if channel["arfcn"] not in unique_channels:
                unique_channels.append(channel["arfcn"])
                unique_channels_list.append(channel)
        channels = unique_channels_list
        scan_time = time.time() - start_time
        logger.log_message(loggerSetup, "INFO", f"Found {len(unique_channels)} unique channels in {scan_time:.2f} seconds")
        return channels, scan_time
    except Exception as e:
        logger.log_message(loggerSetup, "ERROR", f"Error during cell scan: {e}")
        return [], 0

# Function to capture packets using grgsm_livemon_headless
def channel_capture(frequency, sample_rate, logger, loggerSetup):
    logger.log_message(loggerSetup, "DEBUG", f"Starting channel capture on frequency: {frequency} with sample rate: {sample_rate}")
    command = f"grgsm_livemon_headless -f {frequency} -s {sample_rate} --args=hackrf"
    process = subprocess.Popen(command, shell=True, preexec_fn=os.setsid)  # Use os.setsid to create a new process group
    active_processes.append(process)  # Register the process
    return process

# Function to decode packets using tshark
def decode_packets(logger, loggerSetup):
    logger.log_message(loggerSetup, "DEBUG", "Starting packet decoding with tshark")
    command = "sudo tshark -i lo -Y 'e212.imsi' -V"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)  # Use os.setsid
    active_processes.append(process)  # Register the process
    return process

# Function to filter the decoded packets and get the required details
def filter_packets(output, frequency, logger, loggerSetup):
    logger.log_message(loggerSetup, "DEBUG", "Filtering packets for TMSI, ARFCN, Signal Level")
    mobile_stations = []
    lines = output.decode('utf-8').splitlines()  # Decode bytes to string and split into lines
    current_station = {}

    for line in lines:
        line = line.strip()
        if "ARFCN:" in line:
            arfcn = line.split(":")[1].split()[0].strip()
            current_station["arfcn"] = arfcn
        elif "Signal Level:" in line:
            signal_level = line.split(":")[1].strip().split()[0]
            current_station["signal_level"] = signal_level
        elif "TMSI/P-TMSI/M-TMSI/5G-TMSI:" in line:
            tmsi = line.split(":")[1].strip()
            current_station["tmsi"] = tmsi
            mobile_stations.append(current_station)
        elif "Frame" in line and "on interface lo" in line:  # New frame indicates end of current station
            current_station = {}
    logger.log_message(loggerSetup, "INFO", f"Filtered {len(mobile_stations)} mobile stations for the {frequency} frequency")
    return mobile_stations

# Function to run the packet capture and decoding in parallel
def run_capture_and_decode(frequency, sample_rate, cell_timer, logger, loggerSetup):
    try:
        # Start the processes
        capture_process = channel_capture(frequency, sample_rate, logger, loggerSetup)
        decode_process = decode_packets(logger, loggerSetup)
        # Sleep for the specified duration
        time.sleep(cell_timer)

        # Terminate the process groups
        os.killpg(os.getpgid(capture_process.pid), signal.SIGTERM)  # Terminate capture process group
        os.killpg(os.getpgid(decode_process.pid), signal.SIGTERM)  # Terminate decode process group
        logger.log_message(loggerSetup, "DEBUG", f"Terminated capture and decode processes after {cell_timer} seconds for frequency: {frequency}")
    except Exception as e:
        logger.log_message(loggerSetup, "ERROR", f"Error terminating processes: {e}")
    finally:
        # Ensure resources are cleaned up
        capture_process.wait()
        decode_process.wait()
    return capture_process, decode_process

# Function to get unique TMSI from the mobile stations list and filter based on the signal level
def get_unique_ms(mobile_stations, signal_threshold, logger, loggerSetup):
    unique_tmsi = []
    unique_ms = []
    signal_levels = []
    for station in mobile_stations:
        tmsi = station["tmsi"]
        if tmsi not in unique_tmsi:
            unique_tmsi.append(tmsi)
            # store all the signal levels for debugging
            signal_levels.append(station["signal_level"])
            # Check if the signal level is above the threshold
            if int(station["signal_level"]) >= signal_threshold:
                unique_ms.append(station)
    logger.log_message(loggerSetup, "INFO", f"Found {len(unique_tmsi)} unique Mobile Stations")
    logger.log_message(loggerSetup, "DEBUG", f"Observed signal levels: {signal_levels}")
    logger.log_message(loggerSetup, "INFO", f"Nearest Mobile Stations count: {len(unique_ms)}")
    return unique_ms


################ Main function to run the Cellular Occupancy ALO algorithm ###############
def get_cellular_occupancy_list(logger, cellular_properties, system_properties):
    try:
        # setting up logger
        log_prefix = "cellular-occupancy-algo"
        log_module = "Cellular"
        loggerSetup = logger.setup_logger(log_prefix, log_module)
        logger.log_message(loggerSetup, "START", "Starting the Cellular Occupancy Algorithm")
        logger.enable_requests_logging(loggerSetup)

        module_status_code = 1

        # Defining the variables
        channel_list_file_path = "nearby_channels.json"
        bands = cellular_properties["cellular_band"]
        sample_rate = cellular_properties["sdr_sample_rate"]
        signal_threshold = cellular_properties["signal_threshold"]
        cell_scan_expire_time = cellular_properties["cell_scan_expire_time"]
        cell_timer = 0
        scan_time = 0
        mobile_stations = []

        # Read the channel data from the file
        channels = read_channel_file(channel_list_file_path, cell_scan_expire_time, logger, loggerSetup)
        # If the file is empty or not found, run the cell_scan function
        if not channels:
            channels, scan_time = cell_scan(bands, sample_rate, logger, loggerSetup)
            write_channel_file(channel_list_file_path, channels, logger, loggerSetup)
            logger.log_message(loggerSetup, "INFO", f"Using newly scanned channels.")
            # Read the channel data from the file
            channels = read_channel_file(channel_list_file_path, cell_scan_expire_time, logger, loggerSetup)
            if not channels:
                logger.log_message(loggerSetup, "ERROR", f"No channels found after cell scan.")
                return [], module_status_code

        # Calculate cell_timer
        # reduce the cell_timer when performing the cell_scan
        cell_timer = ((system_properties["cloud_sync_interval"] - scan_time) / len(channels)) - 1
        if cell_timer < 0: cell_timer = 0
        logger.log_message(loggerSetup, "INFO", f"Calculated cell timer: {cell_timer} seconds")

        # Loop through the channels and capture packets
        logger.log_message(loggerSetup, "INFO", f"Starting packet capture on {len(channels)} channels...")
        for channel in channels:
            frequency = channel["frequency"]
            capture_process, decode_process = run_capture_and_decode(frequency, sample_rate, cell_timer, logger, loggerSetup)
            if not capture_process or not decode_process:
                continue
            # Get the output from the decode process
            output, _ = decode_process.communicate()
            # Filter the packets and get the mobile stations
            filtered_stations = filter_packets(output, frequency, logger, loggerSetup)
            mobile_stations.extend(filtered_stations)
        logger.log_message(loggerSetup, "INFO", f"Captured {len(mobile_stations)} mobile stations in total")

        # Get unique TMSI from the mobile stations list
        logger.log_message(loggerSetup, "INFO", f"Getting unique TMSI from the mobile stations list...")
        unique_ms = get_unique_ms(mobile_stations, signal_threshold, logger, loggerSetup)

        module_status_code = 0
        logger.log_message(loggerSetup, "END", "Executed the Cellular algorithm")
        return unique_ms, module_status_code
    except Exception as e:
        logger.log_message(loggerSetup, "ERROR", f"Error in Cellular Occupancy Algorithm: {e}")
        return [], module_status_code