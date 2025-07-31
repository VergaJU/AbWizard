#!/bin/bash

# Get the directory where the script is located
# This makes the script runnable from anywhere
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Navigate to the script's directory
cd "$SCRIPT_DIR"

echo "Checking for updates..."
# Pull the latest changes from the main branch on GitHub
# git pull origin main

echo "Starting AbWizard..."
# Activate the virtual environment and run the Python GUI script
source .venv/bin/activate
python AbWizard/gui.py

# Optional: Deactivate when the GUI closes (might not run if GUI is closed abruptly)
deactivate

echo "AbWizard has closed."