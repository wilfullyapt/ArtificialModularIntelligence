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
    [ -d snowboy ] && rm -rf snowboy
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
apt-get update && apt-get install -y python3 python3-pip python3-venv git

# Step 2: Create and activate virtual environment
echo -e "${GREEN}Setting up virtual environment ...${NC}"
python3 -m venv venv
source venv/bin/activate || cleanup_and_exit

trap cleanup_and_exit ERR

# Step 3: Install requirements
echo -e "${GREEN}Installing Python requirements ...${NC}"
pip install -r requirements.txt

sudo -k

# Step 4: Copy config file
echo -e "${GREEN}Setting up configuration file ...${NC}"
[ ! -f config.yaml ] && cp config_template.yaml config.yaml

# Step 5: Install Snowboy
echo -e "${GREEN}Cloning seasalt-ai/snowboy ...${NC}"
if git clone https://github.com/seasalt-ai/snowboy.git; then
    if ! cd snowboy/swig/Python3; then
        echo -e "${RED}Failed to change directory to snowboy/swig/Python3. Exiting.${NC}"
        cleanup_and_exit
    fi
else
    echo -e "${RED}Failed to clone Snowboy repository. Exiting.${NC}"
    cleanup_and_exit
fi

echo -e "${GREEN}Compiling and installing Snowboy ...${NC}"
make || { echo -e "${RED}Failed to make Snowboy.${NC}"; cleanup_and_exit; }
cd ../..
python3 setup.py install || { echo -e "${RED}Failed to install Snowboy.${NC}"; cleanup_and_exit; }

# Step 6: Copy relevant files
echo -e "${GREEN}Copying Snowboy files to virtual environment ...${NC}"
VENV_PATH=$(python -c "import site; print(site.getsitepackages()[0])")
echo " - Virtual environment: ${VENV_PATH}"

SNOWBOY_DIR=$(find ${VENV_PATH} -type d -name "snowboy-*" | head -n 1)
if [ -z "${SNOWBOY_DIR}" ]; then
    echo -e "${RED}Snowboy directory not found. Exiting.${NC}"
    cleanup_and_exit
fi
echo " - Snowboy directory: ${SNOWBOY_DIR}"

cp swig/Python3/_snowboydetect.so ${SNOWBOY_DIR}/snowboy/_snowboydetect.so
mkdir -p ${SNOWBOY_DIR}/snowboy/resources
cp resources/common.res ${SNOWBOY_DIR}/snowboy/resources/common.res

# Cleanup
echo -e "${GREEN}Cleaning up ...${NC}"
cd ..
rm -rf snowboy

# Get the original user who ran the script with sudo
ORIGINAL_USER=$SUDO_USER

# Change ownership of the virtual environment and config.yaml
echo -e "${GREEN}Changing ownership of virtual environment and config.yaml...${NC}"
chown -R $ORIGINAL_USER:$ORIGINAL_USER venv
chown $ORIGINAL_USER:$ORIGINAL_USER config.yaml

trap - ERR

echo -e "${GREEN}Installation completed successfully!${NC}"
deactivate
