@echo off
setlocal enabledelayedexpansion

:: Config file path
set CONFIG_FILE=config.txt

:: Default values (will be overwritten if found in the config file)
set PYTHON_PATH=
set ESPTOOL_PATH=
set VENV_DIR=
set PORT=

:: Load stored config (if it exists)
if exist %CONFIG_FILE% (
    echo Loading stored configuration...
    for /f "tokens=1,2 delims==" %%i in (%CONFIG_FILE%) do (
        if "%%i"=="PYTHON_PATH" set PYTHON_PATH=%%j
        if "%%i"=="ESPTOOL_PATH" set ESPTOOL_PATH=%%j
        if "%%i"=="VENV_DIR" set VENV_DIR=%%j
        if "%%i"=="PORT" set PORT=%%j
    )
)

:: Save configuration to config file
:save_config
(
    echo PYTHON_PATH=%PYTHON_PATH%
    echo ESPTOOL_PATH=%ESPTOOL_PATH%
    echo VENV_DIR=%VENV_DIR%
    echo PORT=%PORT%
) > %CONFIG_FILE%

:: Ask for python path, esptool path, tty port, and virtual environment directory if not already configured
if "%PYTHON_PATH%"=="" (
    set /p PYTHON_PATH="Enter the full path to your Python interpreter: "
)
if "%ESPTOOL_PATH%"=="" (
    set /p ESPTOOL_PATH="Enter the full path to your esptool.py: "
)
if "%VENV_DIR%"=="" (
    set /p VENV_DIR="Enter the directory where you'd like to create the virtual environment: "
)
if "%PORT%"=="" (
    set /p PORT="Enter the serial port (e.g., COM3): "
)

call :save_config

:: Activate virtual environment (Windows)
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Creating virtual environment in %VENV_DIR%...
    %PYTHON_PATH% -m venv "%VENV_DIR%"
)
call "%VENV_DIR%\Scripts\activate.bat"

:: Check and install rshell if needed
where rshell >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo rshell not found. Installing rshell...
    pip install rshell
    if %ERRORLEVEL% neq 0 (
        echo Failed to install rshell.
        exit /b 1
    )
)

echo If your device is already plugged in, please disconnect and reconnect it now! This process will take approx. 3 minutes.
pause

:: Define the esptool.py commands
set ERASE_CMD=%PYTHON_PATH% %ESPTOOL_PATH% -p %PORT% -b 460800 erase_flash
set FLASH_CMD=%PYTHON_PATH% %ESPTOOL_PATH% -p %PORT% -b 460800 --before default_reset --after hard_reset --chip esp32 write_flash --flash_mode dio --flash_size 4MB --flash_freq 40m 0x0 esp32_micropython.bin

:: Target directory containing the configuration files
set TARGET_CONFIG_DIR=iwp

:: Function to check if the port is connected
:check_port
mode %PORT% >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Port %PORT% disconnected. Waiting for reconnection...
    timeout /t 1 >nul
    goto :check_port
)
echo Port %PORT% reconnected.

:: Run the esptool.py commands
echo Running erase_flash...
%ERASE_CMD%
if %ERRORLEVEL% neq 0 (
    echo Erase flash command failed.
    goto :check_port
)

echo Running write_flash...
%FLASH_CMD%
if %ERRORLEVEL% neq 0 (
    echo Write flash command failed.
    goto :check_port
)

:: Step 1: Use rshell to send a native interrupt to stop any running script
echo Sending a native interrupt to stop any running script on the device...
rshell -p %PORT% repl "~\x03~" >nul 2>nul

:: Step 2: Perform the file copy
echo Copying files to device at %PORT%...
rshell -p %PORT% cp --recursive %TARGET_CONFIG_DIR%\* /pyboard/ >nul
if %ERRORLEVEL% neq 0 (
    echo File copy failed.
    goto :check_port
)

:: Step 3: Reset the device after flashing and file copying
echo Resetting the device...
rshell -p %PORT% repl "~\x03~" >nul 2>nul
rshell -p %PORT% repl "~\x04~" >nul 2>nul

:: Optional: Wait for the device to be unplugged before finishing
echo Please unplug the device to complete the process.
:wait_for_unplug
mode %PORT% >nul 2>nul
if %ERRORLEVEL% eq 0 (
    timeout /t 1 >nul
    goto :wait_for_unplug
)

echo Device unplugged. Process complete.

:: Prompt user to continue or exit
:continue_or_exit
set "key="
set /p "key=Press ENTER to flash another device or ESC to exit..." >nul
if "%key%"=="" (
    echo Waiting for the next device to be plugged in...
    goto :check_port
) else (
    exit /b
)
