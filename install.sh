#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if running on Linux
if [ "$(uname)" != "Linux" ]; then
    echo -e "${RED}This script only supports Linux. Windows and MacOS are not supported.${NC}"
    exit 1
fi

# Function to install system dependencies
install_system_deps() {
    if command -v apt-get >/dev/null 2>&1; then
        echo -e "${GREEN}Installing dependencies using apt...${NC}"
        sudo apt-get update
        sudo apt-get install -y \
            python3-venv \
            python3-pip \
            qt6-base-dev \
            python3-pyqt6.sip \
            libportaudio2 \
            portaudio19-dev \
            libsndfile1 \
            protobuf-compiler \
            build-essential \
            curl
    elif command -v dnf >/dev/null 2>&1; then
        echo -e "${GREEN}Installing dependencies using dnf...${NC}"
        sudo dnf install -y \
            python3-devel \
            python3-pip \
            qt6-qtbase-devel \
            python3-qt6 \
            portaudio-libs \
            libsndfile \
            protobuf-compiler \
            gcc \
            gcc-c++ \
            curl
    else
        echo -e "${RED}Unsupported Linux distribution. Please install the following packages manually:${NC}"
        echo "- Python 3.10 or higher"
        echo "- pip"
        echo "- Qt6"
        echo "- PortAudio"
        echo "- libsndfile"
        echo "- protobuf-compiler"
        echo "- build-essential"
        exit 1
    fi
}

# Function to set up Python environment
setup_python_env() {
    echo -e "${GREEN}Setting up Python virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel

    echo -e "${GREEN}Installing Python dependencies...${NC}"
    pip install -e .
}

# Function to set up configuration
setup_config() {
    if [ ! -f config.yaml ]; then
        echo -e "${GREEN}Setting up configuratio\\n file...${NC}"
        cp config_template.yaml config.yaml
    else
        echo -e "${YELLOW}config.yaml already exists, skipping...${NC}"
    fi
}

# Main installation process
echo -e "${GREEN}Starting installation of ArtificialModularIntelligence...${NC}"
echo -e "${YELLOW}Note: This installation script only supports Linux${NC}"

install_system_deps
setup_python_env
setup_config

echo -e "${GREEN}Installation completed successfully!${NC}"
echo -e "${YELLOW}To activate the virtual environment, run:${NC}"
echo -e "source venv/bin/activate"
