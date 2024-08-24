# TODO
'''
Move test functions over here from the driver and import properly
'''
from lib.IS31FL3729 import IS31FL3729
from machine import Pin, I2C
import time

def set_up_led_matrix(i2c=None):
    # Initialize I2C and the LED matrix for our badge
    #i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
    
    # Create the display object with correct cs_currents
    led_matrix = IS31FL3729(i2c)

    # Mod the CS currents for red to be brighter. 
    cs_currents = [0x40] * 14
    cs_currents.append(0xff)

    led_matrix.cs_currents = cs_currents

    # grid-based animations. If this is NOT set you can still write the led_brightness_map
    # Create map of your LEDs. You WILL get a key error if you don't include this
    
    create_led_matrix_map(led_matrix)
    create_led_brightness_map(led_matrix)
    # Set the correct number of cols and rows for 
    led_matrix.rows = 7
    led_matrix.cols = 6
    
    # Initialize/Start the matrix
    led_matrix.start_display()
    
    return led_matrix

def refresh_led_matrix(led_matrix):
    led_matrix.render_led_map()

def create_led_matrix_map(led_matrix):
    # This is the physical representation of the current LED lay out. This is for our custom 6x7 pixel grid display
    # #DO NOT CHANGE
    led_matrix.led_matrix_map = {
        (0, 0): 0x2e, (0, 1): 0x2d, (0, 2): 0x1e, (0, 3): 0x1d, (0, 4): 0x0e, (0, 5): 0x0d, (0, 6): 0x1f,
        (1, 0): 0x2c, (1, 1): 0x2b, (1, 2): 0x1c, (1, 3): 0x1b, (1, 4): 0x0c, (1, 5): 0x0b, (1, 6): 0x0f,
        (2, 0): 0x2a, (2, 1): 0x29, (2, 2): 0x1a, (2, 3): 0x19, (2, 4): 0x0a, (2, 5): 0x09, 
        (3, 0): 0x28, (3, 1): 0x27, (3, 2): 0x18, (3, 3): 0x17, (3, 4): 0x08, (3, 5): 0x07, 
        (4, 0): 0x26, (4, 1): 0x25, (4, 2): 0x16, (4, 3): 0x15, (4, 4): 0x06, (4, 5): 0x05, 
        (5, 0): 0x24, (5, 1): 0x23, (5, 2): 0x14, (5, 3): 0x13, (5, 4): 0x04, (5, 5): 0x03,
        (6, 0): 0x22, (6, 1): 0x21, (6, 2): 0x12, (6, 3): 0x11, (6, 4): 0x02, (6, 5): 0x01
    }
    return led_matrix
    
def create_led_brightness_map(led_matrix):
    #Store the brightness value of the hex address, not the xy coord. 
    led_matrix.led_brightness_map = {
        0x00 : 0 ,  0x01 : 0, 0x02 : 0, 0x03 : 0, 0x04 : 0, 0x05 : 0, 0x06 : 0, 
        0x07 : 0, 0x08 : 0, 0x09 : 0, 0x0a : 0, 0x0b : 0, 0x0c : 0, 0x0d : 0, 
        0x0e : 0, 0x0f : 0, 0x10 : 0, 0x11 : 0, 0x12 : 0, 0x13 : 0, 0x14 : 0, 
        0x15 : 0, 0x16 : 0, 0x17 : 0, 0x18 : 0, 0x19 : 0, 0x1a : 0, 0x1b : 0, 
        0x1c : 0, 0x1d : 0, 0x1e : 0, 0x1f : 0, 0x20 : 0, 0x21 : 0, 0x22 : 0, 
        0x23 : 0, 0x24 : 0, 0x25 : 0, 0x26 : 0, 0x27 : 0, 0x28 : 0, 0x29 : 0, 
        0x2a : 0, 0x2b : 0, 0x2c : 0, 0x2d : 0, 0x2e : 0, 0x2f : 0
    }
    print("Setting default brightness map")
    return led_matrix

def test_turn_on_all_led_matrix(self, brightness=100):
    
    for x in range(7):
        for y in range(6):
            address = self.led_matrix_map[(x,y)]
            self.led_brightness_map[address] = brightness 

    self.render_led_map()
def test_led_matrix(led_matrix):
    for item in led_matrix.led_matrix_map:
        reg = led_matrix.led_matrix_map[item]
        reg_hex = hex(led_matrix.led_matrix_map[item])
        print(f"register: {reg_hex} == {reg}, coord: {item}")
        led_matrix.set_led_raw(reg,255)
        time.sleep_ms(1000)
        a = input("Is this correct? If not you should fix it...")
        led_matrix.set_led_raw(reg,0)

def test_render_led_map(led_matrix): 
    for x in range(0,7):
        for y in range(0,6):
            print(f"Testing coord: {x},{y}")
            address = led_matrix.led_matrix_map[(x,y)]
            led_matrix.led_brightness_map[address] = 255
            led_matrix.render_led_map()
            
            a = input(f"Is this correct? {address} is what we are turning on. If not you should fix it...")
            led_matrix.led_brightness_map[address] = 0
            led_matrix.render_led_map()
