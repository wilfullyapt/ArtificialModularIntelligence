#!/bin/bash
set -e

if [ -z "$BASH_VERSION" ]; then
    echo "Error: This script must be run in a Bash shell."
    exit 1
fi

if ! grep -qi "Raspberry Pi" /proc/cpuinfo && ! grep -qi "Raspberry Pi" /sys/firmware/devicetree/base/model 2>/dev/null; then
    echo "Error: This script is designed for Raspberry Pi. Non-Raspberry Pi system detected."
    exit 1
fi

if ! sudo -n true 2>/dev/null; then
    echo "Error: This script requires sudo privileges to install system dependencies."
    echo "Please run with a user that has sudo access or provide the sudo password."
    exit 1
fi

if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo "Added ~/.local/bin to PATH in ~/.bashrc"
fi

echo "Updating package lists..."
sudo apt update
echo "Installing system dependencies..."
sudo apt install -y build-essential python3 python3-dev python3-pip python3-venv git

if ! command -v uv >/dev/null 2>&1; then
    echo "Installing UV..."
    pip3 install --user uv
fi
REPO_URL="<repository-url>"  # Replace with actual URL
REPO_DIR="ami-repo"
if [ -d "$REPO_DIR" ]; then
    rm -rf "$REPO_DIR"
fi
echo "Cloning repository..."
git clone "$REPO_URL" "$REPO_DIR"
cd "$REPO_DIR"

echo "Running make install..."
make install

echo "Reloading .bashrc..."
source ~/.bashrc

echo "Setup complete! You can now run 'ami' from the command line."
