"""
Written by: BadAask
Written for: DC32
Date started: 20240720
Copyright: Do what you want because a pirate is free

Description: Basic driver for IS31FL3729 chip. 

Driver for the IS31FL3729 LED driver chip using I2C communication.

    Args:
        i2c (I2C): The I2C bus instance.
        address (int): The I2C address of the IS31FL3729 chip (default: 0x34).
        cs_currents (list of int): List of current settings for the current sources (default: [0x40] * 15).
        grid_size_mode (list of int): Grid size mode configuration (default: [0x61]).

    Usage:
        1. Import the necessary modules and create an I2C instance:
            from machine import I2C, Pin
            from IS31FL3729 import IS31FL3729

            i2c = I2C(0, scl=Pin(22), sda=Pin(21))  # Adjust the pins according to your setup

        2. Create an instance of the IS31FL3729 class:
            led_driver = IS31FL3729(i2c)

        3. Initialize and start the display:
            led_driver.start_display()

        4. Map the LEDs to specific coordinates:
            led_driver.map_leds(num_leds=45)
            
           Follow the on-screen prompts to enter the row and column for each LED.
           Once mapped you can hard-code the map in your setup as to avoid doing this each time you
           set it up

        5. Set the brightness of a specific LED by its register:
            led_driver.set_led(0x01, 128)  # Set LED at register 0x01 to half brightness

        6. Set the brightness of an LED using coordinates:
            led_driver.set_led_by_coord(0, 1, 255)  # Set LED at row 0, column 1 to full brightness

        7. Set multiple LEDs using a list of coordinates and brightness values:
            led_list = [(0, 1, 255), (1, 2, 128), (2, 3, 64)]
            led_driver.set_led_list(led_list)

        8. Clear the LED matrix (turn off all LEDs):
            led_driver.clear_matrix()

    Methods:
        i2c_w(reg, data): Write data to a specified register.
        start_display(): Initialize and start the display after setting things up.
        set_led_raw(reg, brightness): Set the brightness of an LED using its register.
        map_leds(num_leds=45): Map LEDs to coordinates by prompting the user.
        render_led_map(): Render the current LED brightness map to the display.
        set_led(reg, brightness): Set the brightness of an LED by its register.
        set_led_by_coord(x, y, brightness): Set the brightness of an LED using coordinates.
        set_led_list(led_list_x_y): Set the brightness of multiple LEDs using a list of coordinates and brightness values.
        clear_matrix(): Clear the LED matrix (turn off all LEDs).
        set_max_brightness(max_brightness): Set the maximum brightness for all LEDs.
"""

import time

class IS31FL3729:
    
    def __init__(self, i2c, address=0x34, cs_currents=[0x40] * 15, grid_size_mode=[0x61]):
        self.i2c = i2c
        self.address = address
        
        self.led_matrix_map = {}
        self.led_brightness_map = {}
        
        self.cs_currents = cs_currents
        self.grid_size_mode = grid_size_mode
        self.max_brightness = 255  # Default maximum brightness
        
        # Initialize the grid dimensions
        self.rows, self.cols = 0, 0

    def i2c_w(self, reg, data):
        buf = bytearray(1)
        buf[0] = reg
        buf.extend(bytearray(data))
        self.i2c.writeto(self.address, buf)

    def start_display(self):
        # Reset all registers
        self.i2c_w(0xcf, [0xae])
        # Set current limit to 16/64
        self.i2c_w(0xa1, [64])
        # Set each current source current
        self.i2c_w(0x90, bytearray(self.cs_currents))
        
        # Enable chip in proper mode, defaults to 3x16 mode
        self.i2c_w(0xa0, self.grid_size_mode)

    def set_led_raw(self, reg, brightness):
        self.i2c_w(reg, [brightness])

    def map_leds(self, num_leds=45):
        leds = [0x00]
        
        for led in num_leds:
            leds.append(led)
            
        for reg in leds:
            self.set_led_raw(reg, 255)  # Turn on the LED
            row = int(input(f"Enter row for LED {hex(reg)}: "))
            col = int(input(f"Enter column for LED {hex(reg)}: "))
            self.led_matrix_map[(row, col)] = reg
            self.set_led_raw(reg, 0)  # Turn off the LED
            time.sleep(0.10)  # Wait a bit before lighting the next LED

        print("Final LED Map:")
        for key, value in sorted(self.led_matrix_map.items()):
            print(f"{key}: {hex(value)}")

    def render_led_map(self):
        led_brightness_list = []
        for i, item in enumerate(self.led_brightness_map):
            brightness_value = min(self.led_brightness_map[item], self.max_brightness)
            led_brightness_list.append(brightness_value)
        length_of_list = len(led_brightness_list)
        self.i2c_w(0x00, led_brightness_list)

    def set_led(self, reg, brightness):
        self.led_brightness_map[reg] = min(brightness, self.max_brightness)
        self.render_led_map()
    
    def set_led_by_coord(self, x, y, brightness):
        reg = hex(self.led_matrix_map[(x, y)])
        self.led_brightness_map[reg] = min(brightness, self.max_brightness)
        self.render_led_map()
        
    def set_led_list(self, led_list_x_y):
        for x, y, brightness in led_list_x_y:
            reg = self.led_matrix_map[(x, y)]
            self.led_brightness_map[reg] = min(brightness, self.max_brightness)
        self.render_led_map()
        
    def clear_matrix(self):
        for led in self.led_brightness_map:
            if led == 16 or led == 32:
                continue
            self.led_brightness_map[led] = 0
        self.render_led_map()

    def set_brightness(self, max_brightness):
        """Set the maximum brightness for all LEDs."""
        self.max_brightness = max_brightness
        self.render_led_map()

