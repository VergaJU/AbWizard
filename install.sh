#!/bin/bash

# --- Configuration ---
PYTHON_CMD="python3" # Use "python" if that's the command on the target system
VENV_DIR="venv"

# --- Main Script ---

echo "Starting AbWizard Setup..."

# Get the absolute path to the directory where this script is located
INSTALL_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$INSTALL_DIR" # Ensure we are running from the project root

# --- Step 1: Check for essential commands (python, git) ---
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "ERROR: Python ($PYTHON_CMD) could not be found. Please install Python 3."
    exit 1
fi
if ! command -v git &> /dev/null; then
    echo "ERROR: Git could not be found. Please install Git."
    exit 1
fi
echo "✓ Essential commands found."

# --- Step 2: Set up the Python Virtual Environment ---
if [ -d "$VENV_DIR" ]; then
    echo "✓ Virtual environment '$VENV_DIR' already exists. Skipping creation."
else
    echo "Creating Python virtual environment in './$VENV_DIR'..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment."
        exit 1
    fi
    echo "✓ Virtual environment created."
fi

# --- Step 3: Activate environment and install dependencies ---
echo "Activating virtual environment and installing dependencies from requirements.txt..."
source "${VENV_DIR}/bin/activate"

pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install Python packages from requirements.txt."
    # Optional: Deactivate before exiting on failure
    deactivate
    exit 1
fi

# Deactivate the environment now that dependencies are installed
deactivate
echo "✓ Dependencies installed successfully."

# --- Step 4: Create and install the .desktop launcher ---
echo "Installing application launcher..."

# Define paths
DESKTOP_ENTRY_SOURCE="${INSTALL_DIR}/abwizard.desktop"
DESKTOP_ENTRY_DEST="${HOME}/.local/share/applications/abwizard.desktop"
RUN_SCRIPT_PATH="${INSTALL_DIR}/run_abwizard.sh"
ICON_PATH="${INSTALL_DIR}/abwizard_icon.png" # Make sure this icon file exists

if [ ! -f "$DESKTOP_ENTRY_SOURCE" ]; then
    echo "ERROR: abwizard.desktop file not found!"
    exit 1
fi

# Use a temporary file for the configured .desktop entry
TEMP_DESKTOP_FILE=$(mktemp)

# Use sed to replace placeholder paths with real absolute paths
sed -e "s|Exec=/path/to/your/project/run_abwizard.sh|Exec=${RUN_SCRIPT_PATH}|" \
    -e "s|Icon=/path/to/your/project/abwizard_icon.png|Icon=${ICON_PATH}|" \
    "$DESKTOP_ENTRY_SOURCE" > "$TEMP_DESKTOP_FILE"

# Ensure the destination directory exists
mkdir -p "${HOME}/.local/share/applications"

# Copy the configured file
cp "$TEMP_DESKTOP_FILE" "$DESKTOP_ENTRY_DEST"

# Clean up
rm "$TEMP_DESKTOP_FILE"

# Make the launcher executable
chmod +x "$DESKTOP_ENTRY_DEST"
echo "✓ Application launcher created."

# --- Final Instructions ---
echo
echo "======================================================"
echo "  AbWizard Installation Complete!"
echo "======================================================"
echo
echo "You can now find 'AbWizard' in your application menu."
echo "If it doesn't appear immediately, you may need to log out and log back in."
echo