import os
from configparser import ConfigParser
import __logger as logger

# Default properties file name
file_name="system.properties"

# Function to load properties from a file
def load_properties(loggerSetup, module:str):
    """
    Loads properties from a file and returns them as a dictionary.
    Args:
        file_name (str): Name of the properties file (default: system.properties).
    Returns:
        dict: Dictionary of properties and their values.
    """
    logger.log_message(loggerSetup, "INFO", f"Loading {module} properties...")
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Define the path to the properties file (located one directory before)
    properties_file_path = os.path.join(project_root, file_name)

    # Check if the file exists
    if not os.path.exists(properties_file_path):
        logger.log_message(loggerSetup, "WARNING", f"{file_name} not found in the project directory. Using default values!")
    else:
        # Parse the properties file
        config = ConfigParser()
        config.read(properties_file_path)
        logger.log_message(loggerSetup, "INFO", f"{module} properties loaded successfully!")
        # Extract values and return as a dictionary
        return {key: eval(value) for key, value in config["DEFAULT"].items()}
