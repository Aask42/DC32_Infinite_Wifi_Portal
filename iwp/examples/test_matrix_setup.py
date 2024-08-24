'''
Written by: Amelia Wietting
Date: 20240717
For: DEF CON 32
Note: This file is TEST CODE and should only be used for testing things
'''
import time
from machine import Pin, I2C
import neopixel
#
import math

from micropython import const

'''
Notes

- SCL (GPIO 21) and SDA (GPIO 22)


TODO
- Write code to test the Neopixel strip
    - led_strip = neopixel.NeoPixel(Pin(LED_PIN), NUM_LEDS)
    - LED_PIN = 25 and NUM_LEDS = 36
    - Enable line for neopixels = GPIO 18
        - Low to disable, High to enable
    
- Write code to test upfiring LEDS
    - There is a shutdown pin for the matrix IC. When it is not needed to be on, set the pin to LOW. Otherwise it needs to be HIGH.
        - Shutdown pin is on GPIO9
        - Low to disable, high to enable
    - On i2c address 0x68
    - https://github.com/mchobby/esp8266-upy/blob/master/is31fl/lib/is31fl3731.py
        

- Write code to test Accelerometer
    - Accelerometer: https://github.com/micropython-Chinese-Community/mpy-lib/tree/master/sensor/LIS2DW12
    - On i2c address 0x32

- Write code to test brightness sensor
    - https://github.com/void3729/Mixly2.0_hyseim/blob/f12550ce6cbb8b6bc311a2740abcfe258b31dc13/resources/app/board/micropython_esp32_mixgope/build/lib/ltr308al.py#L4
    - On i2c address 0xA6
    
- read voltage as needed for battery life estimate / flashing low batt LED 
'''



# Configuration
LED_COUNT = 36          # Number of LED pixels.
LED_PIN = 25            # GPIO pin connected to the pixels.

WS_PWR_PIN = 18
p_ws_leds = Pin(WS_PWR_PIN, Pin.OUT)
p_ws_leds.value(1)
# Create the NeoPixel object
led_strip = neopixel.NeoPixel(Pin(LED_PIN), LED_COUNT)
current_color = "000000"


i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# initialize display using Feather CharlieWing LED 15 x 7
#display = is31f.Matrix(i2c)

p_matrix = Pin(9, Pin.OUT)
p_matrix.value(1)

# class Matrix: Adafruit 16x9 Charlieplexed
# class CharlieBonnet : Adafruit 16x8 Charlieplexed Bonnet

# draw a box on the display
# first draw the top and bottom edges

def i2c_w(reg, data):
    # Write a buffer of data (byte array) to the specified I2C register address.
    buf = bytearray(1)
    buf[0] = reg
    
    buf.extend(bytearray(data))
    #print(buf)
    i2c.writeto(0x34, buf)

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def make_leds_color(color_hex="770000", timeout=0):
        
    r, g, b = hex_to_rgb(color_hex)  
   
    #print(f"make_leds_color {r},{g},{b}")

    for i in range(LED_COUNT):
        led_strip[i] = (r, g, b)
    
    led_strip.write()  # Update the strip
    #await uasyncio.sleep_ms(250)
    time.sleep(timeout)
    
# reset all registers
i2c_w(0xcf, [0xae])

# set current limit to 16/64
i2c_w(0xa1, [8])

# set each current source current
cs_currents = [0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
i2c_w(0x90, bytearray(cs_currents))

# enable chip in 3x16 mode
i2c_w(0xa0, [0x61])

# turn on the first LED
#i2c_w(0x01, [0x80, 0x80, 0xff, 0xff])

def calculate_brightness_color(hex_color, brightness):
    # Convert hex color to RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # Apply brightness
    r = int(r * brightness)
    g = int(g * brightness)
    b = int(b * brightness)
    
    # Convert back to hex
    return "{:02x}{:02x}{:02x}".format(r, g, b)

base_color_hex = "FFFFFF"

while True:
    # Initial color setting

    # Fade in
    for y in range(0x00, 0x88):
        led_list = []

        for x in range(1, 0x2F):
            append_data = y
            #if x == 0x0F or x == 0x1f:
            #    append_data = 0
            led_list.append(append_data)

        i2c_w(0x01, led_list)
        led_list = None
        
        # Adjust LED brightness
        brightness = y / 0x88
        adjusted_color = calculate_brightness_color(base_color_hex, brightness)
        #make_leds_color(adjusted_color)

    # Fade out
    for y in reversed(range(0x00, 0x88)):
        led_list = []

        for x in range(1, 0x2F):
            append_data = y
            #if x == 0x0F or x == 0x1f:
            #    append_data = 0
            led_list.append(append_data)

        i2c_w(0x01, led_list)
        led_list = None
        
        # Adjust LED brightness
        brightness = y / 0x88
        adjusted_color = calculate_brightness_color(base_color_hex, brightness)
        #make_leds_color(adjusted_color)

    # Turn off LEDs
    time.sleep_ms(10)



while True:
    # Test LEDs
    test_timeout = 0.5
    make_leds_color(color_hex = "FF0000",timeout=0.5)
    make_leds_color(color_hex = "00FF00",timeout=0.5)
    make_leds_color(color_hex = "0000FF",timeout=0.5)
