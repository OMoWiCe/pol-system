import os
import logging
from datetime import datetime

# logging level
log_level = logging.INFO

# Function to set up the logger
def setup_logger(log_prefix="log"):
    """
    Sets up the logger instance.
    Creates a logs folder in the project directory and writes logs to a date-appended file.
    Args:
        log_prefix (str): Prefix for the log file name.
    Returns:
        logging.Logger: Configured logger instance.
    """
    # Get the project root directory by navigating two levels up
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Define the logs folder in the project root
    logs_folder = os.path.join(project_root, "logs")
    os.makedirs(logs_folder, exist_ok=True)  # Create folder if it doesn't exist
    # Create a log file with the current date and provided prefix
    log_filename = f"{log_prefix}_{datetime.now().strftime('%Y-%m-%d')}.log"
    log_file_path = os.path.join(logs_folder, log_filename)

    # Create a logger for the module with the given prefix
    logger = logging.getLogger(log_prefix)
    # Remove any existing handlers for the logger
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Set the logger level
    logger.setLevel(log_level)
    # Create a file handler for logging to file
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(log_level)
    # Create a stream handler to also output logs to the console
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    # Create a formatter and set it for both handlers
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # Add both handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger

# Function to log messages with different levels
def log_message(logger, level: str, message: str):
    """
    Logs a message with the specified logging level using the given logger.
    Args:
        logger (logging.Logger): The logger instance to use for logging.
        level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        message (str): The message to log.
    """
    level = level.upper()
    if level == "START":
        logger.info(f"{'-' * 20} \t{message}\t {'-' * 20}")
    elif level == "END":
        logger.info(f"{'-' * 20} \t{message}\t {'-' * 20}")
    elif level == "DEBUG":
        logger.debug(message)
    elif level == "INFO":
        logger.info(message)
    elif level == "WARNING":
        logger.warning(message)
    elif level == "ERROR":
        logger.error(message)
    elif level == "CRITICAL":
        logger.critical(message)
    else:
        raise ValueError(f"Invalid log level: {level}")


# Function to enable debug logging for the 'requests' module
def enable_requests_logging(logger):
    """
    Configures the 'requests' logger to use the same handler as the provided parent logger.
    Args:
        logger (logging.Logger): The parent logger (e.g., logger from main-program or wifi-occupancy-algorithm).
    """
     # Configure 'requests' logger
    requests_logger = logging.getLogger("requests")
    requests_logger.setLevel(log_level)
    for handler in requests_logger.handlers:
        requests_logger.removeHandler(handler)
    for handler in logger.handlers:
        requests_logger.addHandler(handler)

    # Configure 'urllib3' logger
    urllib3_logger = logging.getLogger("urllib3")
    urllib3_logger.setLevel(log_level)
    for handler in urllib3_logger.handlers:
        urllib3_logger.removeHandler(handler)
    for handler in logger.handlers:
        urllib3_logger.addHandler(handler)
