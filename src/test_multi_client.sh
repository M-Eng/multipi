#!/bin/bash

# Check if the number of times to run the command is passed as an argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 <number_of_times>"
    exit 1
fi

n=$1

# Function to handle script termination
cleanup() {
    echo "Stopping all subprocesses..."
    kill 0
    exit
}

# Trap Ctrl+C (SIGINT) and call cleanup function
trap 'cleanup' SIGINT

echo "Starting $n instances of the command in parallel..."

# Start the commands in parallel
for ((i=0; i<n; i++)); do
    python client/main.py -t -d device_$i &
    sleep 0.1
done

# Wait for all subprocesses
wait
