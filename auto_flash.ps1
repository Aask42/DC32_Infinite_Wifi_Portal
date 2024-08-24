# Config file path
$CONFIG_FILE = "./config.txt"

# Default values (will be overwritten if found in the config file)
$PYTHON_PATH = ""
$ESPTOOL_PATH = ""
$VENV_DIR = ""
$PORT = ""

# Load stored config (if it exists)
function Load-Config {
    if (Test-Path $CONFIG_FILE) {
        Write-Host "Loading stored configuration..."
        $config = Get-Content $CONFIG_FILE
        foreach ($line in $config) {
            $key, $value = $line -split "="
            switch ($key) {
                "PYTHON_PATH" { $PYTHON_PATH = $value }
                "ESPTOOL_PATH" { $ESPTOOL_PATH = $value }
                "VENV_DIR" { $VENV_DIR = $value }
                "PORT" { $PORT = $value }
            }
        }
    }
}

# Save configuration to config file
function Save-Config {
    @"
PYTHON_PATH=$PYTHON_PATH
ESPTOOL_PATH=$ESPTOOL_PATH
VENV_DIR=$VENV_DIR
PORT=$PORT
"@ | Set-Content $CONFIG_FILE
    Write-Host "Configuration saved."
}

# Ask for python path, esptool path, tty port, and virtual environment directory if not already configured
function Ask-For-Config {
    if (-not $PYTHON_PATH) {
        $PYTHON_PATH = Read-Host "Enter the full path to your Python interpreter"
    }

    if (-not $ESPTOOL_PATH) {
        $ESPTOOL_PATH = Read-Host "Enter the full path to your esptool.py"
    }

    if (-not $VENV_DIR) {
        $VENV_DIR = Read-Host "Enter the directory where you'd like to create the virtual environment"
    }

    if (-not $PORT) {
        $PORT = Read-Host "Enter the serial port (e.g., COM3)"
    }

    Save-Config
}

# Function to activate the virtual environment
function Activate-Venv {
    $venvActivate = Join-Path $VENV_DIR "Scripts\Activate.ps1"
    if (Test-Path $venvActivate) {
        Write-Host "Activating virtual environment..."
        & $venvActivate
    }
}

# Check and install rshell and create virtual environment if not already done
function Check-Rshell {
    if (-not (Get-Command "rshell" -ErrorAction SilentlyContinue)) {
        Write-Host "rshell not found."

        # Check if virtual environment exists, if not, create it
        if (-not (Test-Path $VENV_DIR)) {
            Write-Host "Creating virtual environment in $VENV_DIR..."
            & $PYTHON_PATH -m venv $VENV_DIR
        }

        Activate-Venv

        # Install rshell inside the virtual environment
        Write-Host "Installing rshell..."
        pip install rshell
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to install rshell."
            exit 1
        }
        Write-Host "rshell has been installed in the virtual environment at $VENV_DIR."
        Save-Config
    }
    else {
        Write-Host "rshell is already installed."
    }
}

# Load the config first
Load-Config

# Ask for python path, esptool path, tty port, and virtual environment directory if not already set
Ask-For-Config

# Check for rshell and set up the virtual environment
Check-Rshell

# Activate the virtual environment before running commands
Activate-Venv

Write-Host "If your device is already plugged in, please disconnect and reconnect it now! This process will take approx. 3 minutes."
Start-Sleep -Seconds 5

# Define the esptool.py commands
$ERASE_CMD = "$PYTHON_PATH $ESPTOOL_PATH -p $PORT -b 460800 erase_flash"
$FLASH_CMD = "$PYTHON_PATH $ESPTOOL_PATH -p $PORT -b 460800 --before default_reset --after hard_reset --chip esp32 write_flash --flash_mode dio --flash_size 4MB --flash_freq 40m 0x0 esp32_micropython.bin"

# Target directory containing the configuration files
$TARGET_CONFIG_DIR = "./iwp"

# Function to check if the port is connected
function Is-Port-Connected {
    try {
        [System.IO.Ports.SerialPort]::GetPortNames() -contains $PORT
    } catch {
        return $false
    }
}

# Function to copy files to the MicroPython device
function Copy-Files {
    param (
        [string]$port,
        [string]$config_dir
    )

    if (Test-Path $config_dir) {
        Write-Host "Copying files to device at $port with config $config_dir..."
        rshell -p $port cp --recursive "$config_dir/*" /pyboard/
        Write-Host "Files copied to device at $port."
    }
    else {
        Write-Host "Configuration directory $config_dir not found. Exiting..."
        exit 1
    }
}

# Main loop to monitor port connection status
while ($true) {
    if (-not (Is-Port-Connected)) {
        Write-Host "Port $PORT disconnected. Waiting for reconnection..."
        Start-Sleep -Seconds 1
    }
    else {
        Write-Host "Port $PORT reconnected. Running esptool.py commands..."

        # Run the erase flash command
        Write-Host "Running erase_flash..."
        Invoke-Expression $ERASE_CMD
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Erase flash command failed."
            continue
        }

        # Run the write flash command
        Write-Host "Running write_flash..."
        Invoke-Expression $FLASH_CMD
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Write flash command failed."
            continue
        }

        # Step 1: Use rshell to send a native interrupt to stop any running script
        Write-Host "Sending a native interrupt to stop any running script on the device..."
        rshell -p $PORT repl "~\x03~" | Out-Null

        # Step 2: Perform the file copy
        Copy-Files -port $PORT -config_dir $TARGET_CONFIG_DIR

        # Step 3: Reset the device after flashing and file copying
        Write-Host "Resetting the device..."
        rshell cp ./main.py /pyboard/main.py
        rshell "repl ~ import machine ~ machine.soft_reset() ~"

        # Optional: Wait for the device to be unplugged before finishing
        Write-Host "Please unplug the device to complete the process."
        while (Is-Port-Connected) {
            Start-Sleep -Seconds 1
        }

        Write-Host "Device unplugged. Process complete."

        # Prompt user to continue or exit
        while ($true) {
            $key = Read-Host "Press ENTER to flash another device or ESC to exit"
            if ($key -eq "") {
                Write-Host "Waiting for the next device to be plugged in..."
                break
            }
            elseif ($key -eq "ESC") {
                Write-Host "Exiting the flashing program."
                exit
            }
        }
    }
}
