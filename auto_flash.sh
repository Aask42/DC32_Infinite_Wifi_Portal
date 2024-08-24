#!/bin/bash

# Config file path
CONFIG_FILE="./config.txt"

# Default values (will be overwritten if found in the config file)
PYTHON_PATH=""
ESPTOOL_PATH=""
VENV_DIR=""
PORT=""

# Load stored config (if it exists)
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        echo "Loading stored configuration..."
        while IFS="=" read -r key value; do
            if [ "$key" == "PYTHON_PATH" ]; then
                PYTHON_PATH=$value
            elif [ "$key" == "ESPTOOL_PATH" ]; then
                ESPTOOL_PATH=$value
            elif [ "$key" == "VENV_DIR" ]; then
                VENV_DIR=$value
            elif [ "$key" == "PORT" ]; then
                PORT=$value
            fi
        done < "$CONFIG_FILE"
    fi
}

# Save configuration to config file
save_config() {
    echo "PYTHON_PATH=$PYTHON_PATH" > "$CONFIG_FILE"
    echo "ESPTOOL_PATH=$ESPTOOL_PATH" >> "$CONFIG_FILE"
    echo "VENV_DIR=$VENV_DIR" >> "$CONFIG_FILE"
    echo "PORT=$PORT" >> "$CONFIG_FILE"
    echo "Configuration saved."
}

# Ask for python path, esptool path, tty port, and virtual environment directory if not already configured
ask_for_config() {
    if [ -z "$PYTHON_PATH" ]; then
        read -p "Enter the full path to your Python interpreter: " PYTHON_PATH
    fi

    if [ -z "$ESPTOOL_PATH" ]; then
        read -p "Enter the full path to your esptool.py: " ESPTOOL_PATH
    fi

    if [ -z "$VENV_DIR" ]; then
        read -p "Enter the directory where you'd like to create the virtual environment: " VENV_DIR
    fi

    if [ -z "$PORT" ]; then
        read -p "Enter the serial port (e.g., /dev/ttyUSB0 or /dev/tty.usbserial-110): " PORT
    fi

    save_config
}

# Function to activate the virtual environment
activate_venv() {
    # Activate the virtual environment based on OS
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        source "$VENV_DIR/Scripts/activate"
    else
        # Unix-like system
        source "$VENV_DIR/bin/activate"
    fi
}

# Check and install rshell and create virtual environment if not already done
check_rshell() {
    if ! command -v rshell &> /dev/null; then
        echo "rshell not found."

        # Check if virtual environment exists, if not, create it
        if [ ! -d "$VENV_DIR" ]; then
            echo "Creating virtual environment in $VENV_DIR..."
            $PYTHON_PATH -m venv "$VENV_DIR"
        fi

        # Activate the virtual environment
        echo "Activating virtual environment..."
        activate_venv

        # Install rshell inside the virtual environment
        echo "Installing rshell..."
        pip install rshell
        if [ $? -ne 0 ]; then
            echo "Failed to install rshell."
            exit 1
        fi
        echo "rshell has been installed in the virtual environment at $VENV_DIR."

        save_config
    else
        echo "rshell is already installed."
    fi
}

# Load the config first
load_config

# Ask for python path, esptool path, tty port, and virtual environment directory if not already set
ask_for_config

# Check for rshell and set up the virtual environment
check_rshell

# Activate the virtual environment before running commands
echo "Activating virtual environment for the session..."
activate_venv

echo "If your device is already plugged in, please disconnect and reconnect it now! This process will take approx. 3 minutes. "

# Define the esptool.py commands
ERASE_CMD="$PYTHON_PATH $ESPTOOL_PATH -p $PORT -b 460800 erase_flash"
FLASH_CMD="$PYTHON_PATH $ESPTOOL_PATH -p $PORT -b 460800 --before default_reset --after hard_reset --chip esp32 write_flash --flash_mode dio --flash_size 4MB --flash_freq 40m 0x0 esp32_micropython.bin"

# Target directory containing the configuration files
TARGET_CONFIG_DIR="./iwp"

# Function to check if the port is connected
is_port_connected() {
    ls $PORT &> /dev/null
    return $?
}

# Function to copy files to the MicroPython device
copy_files() {
    local port=$1
    local config_dir=$2
    
    # Check if the configuration directory exists
    if [ -d "$config_dir" ]; then
        echo "Copying files to device at ${port} with config ${config_dir}..."
        # Use rshell to copy files to the ESP32
        rshell -p ${port} cp --recursive ${config_dir}/* /pyboard/
        echo "Files copied to device at ${port}."
    else
        echo "Configuration directory ${config_dir} not found. Exiting..."
        exit 1
    fi
}

# Main loop to monitor port connection status
while true; do
    if ! is_port_connected; then
        echo "Port $PORT disconnected. Waiting for reconnection..."
        while ! is_port_connected; do
            sleep 1
        done
        echo "Port $PORT reconnected. Running esptool.py commands..."

        # Run the erase flash command
        echo "Running erase_flash..."
        $ERASE_CMD
        if [ $? -ne 0 ]; then
            echo "Erase flash command failed."
            continue
        fi

        # Run the write flash command
        echo "Running write_flash..."
        $FLASH_CMD
        if [ $? -ne 0 ]; then
            echo "Write flash command failed."
            continue
        fi

        # Step 1: Use rshell to send a native interrupt to stop any running script
        echo "Sending a native interrupt to stop any running script on the device..."
        rshell -p ${PORT} repl "~\x03~" &> /dev/null

        # Give some time for the interruption to take effect
        sleep 1

        # Step 2: Perform the file copy
        copy_files "${PORT}" "${TARGET_CONFIG_DIR}"

        # Step 3: Reset the device after flashing and file copying
        echo "Resetting the device..."
        rshell cp ./main.py /pyboard/main.py
        rshell "repl ~ import machine ~ machine.soft_reset() ~"

        # Optional: Wait for the device to be unplugged before finishing
        echo "Please unplug the device to complete the process."
        while [ -e "${PORT}" ]; do
            sleep 1
        done

        echo "Device unplugged. Process complete."

        # Prompt user to continue or exit
        while true; do
            read -n 1 -s -r -p "Press ENTER to flash another device or ESC to exit..." key
            if [[ $key == $'\e' ]]; then
                echo -e "\nExiting the flashing program."
                exit 0
            elif [[ $key == "" ]]; then
                echo -e "\nWaiting for the next device to be plugged in..."
                break
            fi
        done
    fi
    sleep 1
done
