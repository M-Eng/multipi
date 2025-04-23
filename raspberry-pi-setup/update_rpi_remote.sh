#!/bin/bash

# Check if an argument was provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <raspberry_pi_list_file>"
    exit 1
fi

# The file containing the list of Raspberry Pi addresses
RASPBERRY_PI_LIST_FILE="$1"

echo "Content of the list file:"
cat "${RASPBERRY_PI_LIST_FILE}"

# Path to the directory containing the files to transfer
SOURCE_DIR="../"

# Path to the directory on the Raspberry Pi where files will be transferred
DESTINATION_DIR="/home/work/multipi"

# Path to the update script on the Raspberry Pi
UPDATE_SCRIPT_ON_PI="/home/work/multipi/src/client/update_client.sh"

USERNAME="cvlab"

# File containing the list of directories to ignore
IGNORE_DIRS_FILE="ignore_dirs.txt"

# Start of the rsync command
RSYNC_COMMAND="rsync -r -e ssh --rsync-path='sudo rsync'"

# Add each directory to ignore to the rsync command
while IFS= read -r IGNORE_DIR; do
    RSYNC_COMMAND+=" --exclude ${IGNORE_DIR}"
done < "${IGNORE_DIRS_FILE}"

# Open the list file using file descriptor 3
exec 3< "${RASPBERRY_PI_LIST_FILE}"

# Loop through each line in the list file using file descriptor 3
while IFS= read -r -u 3 RASPBERRY_PI_ADDRESS; do
    # Skip empty lines and lines starting with #
    if [ -z "${RASPBERRY_PI_ADDRESS}" ] || [[ "${RASPBERRY_PI_ADDRESS}" == "#"* ]]; then
        continue
    fi

    echo "Updating ${RASPBERRY_PI_ADDRESS}..."

    # Create the destination directory if it doesn't exist
    echo "Running SSH mkdir command on ${RASPBERRY_PI_ADDRESS}..."
    ssh "${USERNAME}@${RASPBERRY_PI_ADDRESS}" "sudo mkdir -p ${DESTINATION_DIR}"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create directory on ${RASPBERRY_PI_ADDRESS}"
        continue
    fi

    # Add the source and destination to the rsync command
    FULL_RSYNC_COMMAND="${RSYNC_COMMAND} '${SOURCE_DIR}/'* '${USERNAME}@${RASPBERRY_PI_ADDRESS}:${DESTINATION_DIR}'"

    echo "Rsync command: ${FULL_RSYNC_COMMAND}"

    # Copy the updated code and service files to Raspberry Pi
    echo "Running rsync command..."
    eval $FULL_RSYNC_COMMAND
    if [ $? -ne 0 ]; then
        echo "Error: Rsync command failed for ${RASPBERRY_PI_ADDRESS}"
        continue
    fi

    # Execute the update script on the Raspberry Pi
    echo "Running update script on ${RASPBERRY_PI_ADDRESS}..."
    ssh "${USERNAME}@${RASPBERRY_PI_ADDRESS}" "bash ${UPDATE_SCRIPT_ON_PI}"
    if [ $? -ne 0 ]; then
        echo "Error: Update script failed on ${RASPBERRY_PI_ADDRESS}"
        continue
    fi

    echo "Update sent to ${RASPBERRY_PI_ADDRESS}."
    echo "--------------------------------------------"
done

# Close the file descriptor 3
exec 3<&-

echo "All Raspberry Pis have been processed."
