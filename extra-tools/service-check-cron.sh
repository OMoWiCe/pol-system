#!/bin/bash

# Cron job entry: (Check every minute)
# */1 * * * * cd /root/research-work/pol-system/extra-tools && ./service-check-cron.sh


# check if the process is running
if ps aux | grep -v grep | grep "main-program.py" > /dev/null
then
    if [ "$1" != "stop" ]; then
        echo "OMoWiCe Program is already running"
    fi
else
    if [ "$1" == "stop" ]; then
        echo "OMoWiCe Program is already stopped"
        exit 0
    fi
    # add a log entry with timestamp
    echo "$(date) - OMoWiCe Program is not running, starting it now" >> ../logs/service-check.log
    # start the process
    cd ..
    rm -rf nohup.out
    nohup ./main-program.py > /dev/null 2>&1 &
    # wait for a few seconds to ensure the process has started
    sleep 5
    # check if the process started successfully
    if ps aux | grep -v grep | grep "main-program.py" > /dev/null
    then
        echo "$(date) - OMoWiCe Program has started successfully" >> logs/service-check.log
    else
        echo "$(date) - OMoWiCe Program failed to start" >> logs/service-check.log
        exit 1
    fi
fi

# can pass stop as an argument to stop the process
if [ "$1" == "stop" ]; then
    # get the process ID of the main program
    PID=$(ps aux | grep -v grep | grep "main-program.py" | awk '{print $2}')
    # send SIGINT (Ctrl+C) to the main program process
    kill -2 $PID

    echo "$(date) - OMoWiCe Program has stopped manually" >> ../logs/service-check.log
fi