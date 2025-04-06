#!/root/research-work/venv/bin/python

from azure.iot.device import IoTHubDeviceClient, Message
import json
import _logger as logger

def send_to_iothub(data, connection_string, loggerSetup):
    send_status_code = 1
    logger.log_message(loggerSetup, "DEBUG", "Preparing to send data to IoT Hub...")
    client = IoTHubDeviceClient.create_from_connection_string(connection_string)
    logger.log_message(loggerSetup, "DEBUG", "Connection to IoT Hub established.")

    # Serialize and prepare the message
    logger.log_message(loggerSetup, "DEBUG", "Serializing data to JSON format...")
    message = Message(json.dumps(data))
    message.content_encoding = "utf-8"
    message.content_type = "application/json"

    # Send the message
    logger.log_message(loggerSetup, "DEBUG", "Sending message to IoT Hub...")
    try:
        client.send_message(message)
        send_status_code = 0
        client.shutdown()
        logger.log_message(loggerSetup, "DEBUG", "Connection to IoT Hub closed.")
        return send_status_code
    except Exception as e:
        logger.log_message(loggerSetup, "ERROR", f"Failed to send data to cloud: {e}")
        client.shutdown()
        logger.log_message(loggerSetup, "DEBUG", "Connection to IoT Hub closed.")
        return send_status_code
