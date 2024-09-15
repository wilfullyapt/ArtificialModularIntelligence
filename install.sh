#!/bin/bash

# Define colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

cleanup_and_exit() {
    # Function to clean up and exit
    echo -e "${RED}An error occurred. Cleaning up...${NC}"
    deactivate 2>/dev/null
    [ -f config.yaml ] && rm config.yaml
    [ -d venv ] && rm -rf venv
    exit 1
}

echo -e "${GREEN}Starting installation of ArtificialModularIntelligence...${NC}"

# Check if the script is run with sudo
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root or with sudo.${NC}"
  exit 1
fi

# Step 1: Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
apt-get update && apt-get install -y 
python3.10 python3-pip python3-venv git portaudio19-dev build-essential

# Step 2: Create and activate virtual environment
echo -e "${GREEN}Setting up virtual environment ...${NC}"
python3.10 -m venv venv
source venv/bin/activate || cleanup_and_exit

trap cleanup_and_exit ERR

# Step 3: Install requirements
echo -e "${GREEN}Installing Python requirements ...${NC}"
pip install -r requirements.txt

sudo -k

# Step 4: Copy config file
echo -e "${GREEN}Setting up configuration file ...${NC}"
[ ! -f config.yaml ] && cp config_template.yaml config.yaml

# Get the original user who ran the script with sudo
ORIGINAL_USER=$SUDO_USER

# Change ownership of the virtual environment and config.yaml
echo -e "${GREEN}Changing ownership of virtual environment and config.yaml...${NC}"
chown -R $ORIGINAL_USER:$ORIGINAL_USER venv
chown $ORIGINAL_USER:$ORIGINAL_USER config.yaml

trap - ERR

echo -e "${GREEN}Installation completed successfully!${NC}"
deactivate
