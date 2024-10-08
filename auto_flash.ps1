# Config file path
$CONFIG_FILE = "./config.txt"

# Default values (will be overwritten if found in the config file)
$script:PYTHON_PATH = ""
$script:ESPTOOL_PATH = ""
$script:VENV_DIR = ""
$script:PORT = ""

# Load stored config (if it exists)
function Load-Config {
    if (Test-Path $CONFIG_FILE) {
        Write-Host "Loading stored configuration..."
        $config = Get-Content $CONFIG_FILE
        foreach ($line in $config) {
            # Trim the input to avoid whitespace issues
            $line = $line.Trim()
            if ($line -match "=") {
                $key, $value = $line -split "="
                $key = $key.Trim()
                $value = $value.Trim()
                # Only assign values if they exist
                switch ($key) {
                    "PYTHON_PATH" { if (-not $script:PYTHON_PATH) { $script:PYTHON_PATH = $value } }
                    "ESPTOOL_PATH" { if (-not $script:ESPTOOL_PATH) { $script:ESPTOOL_PATH = $value } }
                    "VENV_DIR" { if (-not $script:VENV_DIR) { $script:VENV_DIR = $value } }
                    "PORT" { if (-not $script:PORT) { $script:PORT = $value } }
                }
            }
        }
    } else {
        Write-Host "Config file not found. Creating a new config."
    }
}

# Save configuration to config file
function Save-Config {
    # Ensure values are retained, and only those updated by the user are modified
    $configContent = @"
PYTHON_PATH=$script:PYTHON_PATH
ESPTOOL_PATH=$script:ESPTOOL_PATH
VENV_DIR=$script:VENV_DIR
PORT=$script:PORT
"@
    $configContent.Trim() | Set-Content $CONFIG_FILE
    Write-Host "Configuration saved."
}

# Ask for python path, esptool path, and virtual environment directory if not already configured
function Ask-For-Config {
    if (-not $script:PYTHON_PATH) {
        $script:PYTHON_PATH = Read-Host "Enter the full path to your Python interpreter"
    }

    if (-not $script:ESPTOOL_PATH) {
        $script:ESPTOOL_PATH = Read-Host "Enter the full path to your esptool.py"
    }

    if (-not $script:VENV_DIR) {
        $script:VENV_DIR = Read-Host "Enter the directory where you'd like to create the virtual environment"
    }

    Save-Config
}

# Function to activate the virtual environment
function Activate-Venv {
    # Use Join-Path for better cross-platform compatibility
    $venvActivatePS = Join-Path $script:VENV_DIR "Scripts\Activate.ps1"
    $venvActivateBat = Join-Path $script:VENV_DIR "Scripts\Activate.bat"
    $venvActivateSh = Join-Path $script:VENV_DIR "bin/activate"

    # Check for the appropriate virtual environment activation script
    if (Test-Path $venvActivatePS) {
        Write-Host "Activating virtual environment from: $venvActivatePS"
        & $venvActivatePS
    } elseif (Test-Path $venvActivateBat) {
        Write-Host "Activating virtual environment from: $venvActivateBat"
        cmd.exe /c $venvActivateBat
    } elseif (Test-Path $venvActivateSh) {
        Write-Host "Activating virtual environment from: $venvActivateSh"
        source $venvActivateSh
    } else {
        Write-Host "Could not find a valid activate script for the virtual environment."
        exit 1
    }
}

# Check and install mpremote and create virtual environment if not already done
function Check-Mpremote {
    if (-not (Get-Command "mpremote" -ErrorAction SilentlyContinue)) {
        Write-Host "mpremote not found."

        # Check if virtual environment exists, if not, create it
        if (-not (Test-Path $script:VENV_DIR)) {
            Write-Host "Creating virtual environment in $script:VENV_DIR..."
            & $script:PYTHON_PATH -m venv $script:VENV_DIR
        }

        Activate-Venv

        # Install mpremote inside the virtual environment
        Write-Host "Installing mpremote..."
        pip install mpremote
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to install mpremote."
            exit 1
        }
        Write-Host "mpremote has been installed in the virtual environment at $script:VENV_DIR."
        Save-Config
    } else {
        Write-Host "mpremote is already installed."
    }
}

# Function to detect available serial ports
function Detect-Port {
    $availablePorts = [System.IO.Ports.SerialPort]::GetPortNames()
    
    if ($availablePorts.Length -eq 0) {
        Write-Host "No serial ports detected. Please plug in your device."
        Read-Host "Press ENTER when the device is connected"
        return Detect-Port
    } elseif ($availablePorts.Length -eq 1) {
        $script:PORT = $availablePorts[0]
        Write-Host "Detected port: $script:PORT"
    } else {
        Write-Host "Multiple ports detected:"
        $availablePorts | ForEach-Object { Write-Host "- $_" }
        $script:PORT = Read-Host "Enter the correct port (e.g., COM3)"
    }

    Save-Config
}

# Load the config first
Load-Config

# Ask for python path, esptool path, and virtual environment directory if not already set
Ask-For-Config

# Detect the port if not already set
if (-not $script:PORT) {
    Detect-Port
}

# Check for mpremote and set up the virtual environment
Check-Mpremote

# Activate the virtual environment before running commands
# Activate-Venv

Write-Host "If your device is already plugged in, please disconnect and reconnect it now! This process will take approx. 3 minutes."
Start-Sleep -Seconds 1

# Define the esptool.py commands
$ERASE_CMD = "$script:PYTHON_PATH $script:ESPTOOL_PATH -p $script:PORT -b 460800 erase_flash"
$FLASH_CMD = "$script:PYTHON_PATH $script:ESPTOOL_PATH -p $script:PORT -b 460800 --before default_reset --after hard_reset --chip esp32 write_flash --flash_mode dio --flash_size 4MB --flash_freq 40m 0x0 esp32_micropython.bin"

# Target directory containing the configuration files
$TARGET_CONFIG_DIR = "./iwp"
$TARGET_CONFIG_DIR = $(get-item $TARGET_CONFIG_DIR).FullName

# Function to copy files to the MicroPython device using mpremote
function Copy-Files {
    param (
        [string]$port,
        [string]$config_dir
    )
    # Check if the configuration directory exists

    # Check if the configuration directory exists
    # Check if the configuration directory exists
    # Check if the configuration directory exists
    if (Test-Path $config_dir) {
        Write-Host "Copying files to device at $port with config $config_dir..."

        # Initialize a hash set to keep track of created directories
        $createdDirs = @{}

        # Get all files in the configuration directory, including subdirectories
        Get-ChildItem -Path $config_dir -Recurse -File | ForEach-Object {
            # Construct the relative path of the file
            $relativePath = $_.FullName.Substring($config_dir.Length).TrimStart("\")
            
            # Construct the remote directory path
            $remoteDir = Split-Path -Path $relativePath -Parent
            
            # Skip root level directories (which would be represented as an empty path in this context)
            if (-not [string]::IsNullOrEmpty($remoteDir)) {
                $remoteDirCommand = ":/$remoteDir"

                # Check if the directory has already been created
                if (-not $createdDirs.ContainsKey($remoteDirCommand)) {
                    Write-Host "Creating directory on device: $remoteDirCommand"
                    try {
                        mpremote connect $port fs mkdir $remoteDirCommand
                        # Mark this directory as created
                        $createdDirs[$remoteDirCommand] = $true
                    } catch {
                        Write-Host "Directory already exists or could not be created: $remoteDirCommand"
                    }
                }
            }
            
            # Copy the file to the remote device with force option to overwrite
            Write-Host "Copying file to device: $relativePath"
            $localFilePath = $_.FullName
            mpremote connect $port fs cp $localFilePath :$relativePath

            Write-Host "File copied: $relativePath"
        }

        Write-Host "Files copied to device at $port."
    } else {
        Write-Host "Configuration directory $config_dir not found. Exiting..."
        exit 1
    }

}

# Main loop to monitor port connection status and run flashing commands
while ($true) {
    try {
        # Check if the port is connected
        if (-not ([System.IO.Ports.SerialPort]::GetPortNames() -contains $script:PORT)) {
            Write-Host "Port $script:PORT disconnected. Waiting for reconnection..."
            Start-Sleep -Seconds 1
            continue
        }
        
        Write-Host "Port $script:PORT reconnected. Running esptool.py commands..."

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

        # Send a soft reset command using mpremote
        Write-Host "Resetting the device..."
        mpremote connect $script:PORT soft-reset

        # Perform the file copy using mpremote
        Copy-Files -port $script:PORT -config_dir $TARGET_CONFIG_DIR

        # Wait for the device to be unplugged before finishing
        mpremote connect $script:PORT soft-reset

        Write-Host "Please POWER CYCLE the device to complete the process."

        # Prompt user to continue or exit
        while ($true) {
            $key = Read-Host "Press ANY KEY to flash another device or CTRL+C to exit"
            if ($key -eq "") {
                Write-Host "Waiting for the next device to be plugged in..."
                break
            }
        }
    }
    catch {
        Write-Host "An error occurred: $_"
        exit 1
    }
}
