import subprocess

def check_devices(logger,loggerSetup):
    # Check if two external WiFi adapters are connected
    wifi_adapters = subprocess.check_output("lsusb | grep -e 'Wireless Adapter' -e '802.11ac NIC'", shell=True).decode().strip()
    logger.log_message(loggerSetup, "DEBUG", f"Connected WiFi adapters: {wifi_adapters}")
    wifi_adapters_count = len(wifi_adapters.split('\n')) if wifi_adapters else 0
    if wifi_adapters_count < 2:
        logger.log_message(loggerSetup, "ERROR", "Less than two external WiFi adapters are connected.")
        return 1
    else:
        logger.log_message(loggerSetup, "INFO", f"Number of external WiFi adapters connected: {wifi_adapters_count}")

    # Check if HackRF device is connected
    hackrf_device = subprocess.check_output("lsusb | grep HackRF", shell=True).decode().strip()
    logger.log_message(loggerSetup, "DEBUG", f"Connected SDR device: {hackrf_device}")
    if not hackrf_device:
        logger.log_message(loggerSetup, "ERROR", "SDR device is not connected.")
        return 1
    else:
        logger.log_message(loggerSetup, "INFO", "SDR device is connected.")

    return 0