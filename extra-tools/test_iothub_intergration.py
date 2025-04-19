#!/root/research-work/pol-system/venv/bin/python

from azure.iot.device import IoTHubDeviceClient, Message
import json
import os
from dotenv import load_dotenv

# read the connection string from environment variable stored one directory before
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Function to send data to Azure IoT Hub
def send_to_iothub(data, connection_string):
    send_status_code = 1
    print("DEBUG", "Preparing to send data to IoT Hub...")
    client = IoTHubDeviceClient.create_from_connection_string(connection_string)
    print("DEBUG", "Connection to IoT Hub established.")

    # Serialize and prepare the message
    print("DEBUG", "Serializing data to JSON format...")
    message = Message(json.dumps(data))
    message.content_encoding = "utf-8"
    message.content_type = "application/json"

    # Send the message
    print("DEBUG", "Sending message to IoT Hub...")
    try:
        client.send_message(message)
        send_status_code = 0
        client.shutdown()
        print("DEBUG", "Connection to IoT Hub closed.")
        return send_status_code
    except Exception as e:
        print("ERROR", f"Failed to send data to cloud: {e}")
        client.shutdown()
        print("DEBUG", "Connection to IoT Hub closed.")
        return send_status_code

# Test the function
if __name__ == "__main__":
    connection_string = os.getenv("IOT_HUB_CONNECTION_STRING")
    data = {
    "location_id": "fot",
    "device_id": "prototype-pol-fot-pi-3772b5ca9cf701ae",
    "utc_timestamp": "2025-04-19T06:38:16.361761+00:00",
    "local_timestamp": "2025-04-19T12:08:16.361790",
    "wifi_occupancy_list": [
        "dwadawdaw", "dwadaw", "dfawdawd", "dfawdad", "dawdaw","dwadawdaw", "dwadaw", "dfawdawd", "dfawdad", "dawdaw","dwadawdaw", "dwadaw", "dfawdawd", "dfawdad", "dawdaw","dwadawdaw", "dwadaw", "dfawdawd", "dfawdad", "dawdaw","dwadawdaw", "dwadaw", "dfawdawd", "dfawdad", "dawdaw"
    ],
    "cellular_occupancy_list": [
        "dwadawdaw", "dwadaw", "dfawdawd", "dfawdad"
    ]
}
    send_status = send_to_iothub(data, connection_string)
    print(f"Send status code: {send_status}")