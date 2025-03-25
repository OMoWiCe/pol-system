#!/bin/bash

# Define variables
# COMMAND="kismet -c wlan24g:name=Wifi-2.4GHz -c wlan5g:name=Wifi-5GHz"
COMMAND="kismet --override pol"
LOG_FILE="../../logs/kismet.log"
PID_FILE="/tmp/kismet_scan.pid"

start_scan() {
    if [ -f "$PID_FILE" ]; then
        echo "Scan is already running with PID $(cat $PID_FILE)."
        exit 1
    fi

    echo "Starting Kismet scan..."
    nohup $COMMAND > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Kismet scan started. Logs are redirected to $LOG_FILE."
}

stop_scan() {
    if [ ! -f "$PID_FILE" ]; then
        echo "No running scan found."
        exit 1
    fi

    PID=$(cat "$PID_FILE")
    echo "Stopping Kismet scan with PID $PID..."
    kill $PID && rm -f "$PID_FILE"
    echo "Kismet scan stopped."
}

case "$1" in
    start)
        start_scan
        ;;
    stop)
        stop_scan
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        exit 1
        ;;
esac
