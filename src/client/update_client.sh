#!/bin/bash

# Navigate to the application directory
cd /home/work/multipi/src/client


# Step 1: Update dependencies
echo "Installing new dependencies..."
sudo pip install -r requirements.txt

cd /home/work/multipi/src/client
pwd

# Step 2: Update Service File (if exists and changed)
if [ -f multipi-client.service ]; then
    echo "Service file found, updating..."
    sudo cp multipi-client.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl restart multipi-client
fi


# # Stepseboot