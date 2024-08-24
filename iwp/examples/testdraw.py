# Draw a box on the edge of the display.
#
import math
import time
from machine import Pin, I2C


# Todo:
'''

Write LED driver for matrixed LEDs

Write driver for Accelerometer

Write driver for Light sensor

Write library for LED animations

# Write logic for cycling animations using the button

# Write button handler so we can handle single, double, triple, and long presses

# Write logic for alphabet on the matrix

# Write library for syncing the firing LEDs using an MQ and currrent millisecond

# change current sink for green and red 

'''

from lib.IS31FL3729 import IS31FL3729

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

led_matrix = IS31FL3729(i2c)

def step_through_leds():
    for reg in range(0,46):
        led_matrix.set_led(reg, 255)
        #hit_enter = input(f"You are on hex address {reg} Hit ENTER to continue")
        time.sleep_ms(10)
        
    for reg in reversed(range(0,46)):
        led_matrix.set_led(reg, 0)
        #hit_enter = input(f"You are on hex address {reg} Hit ENTER to continue")
        time.sleep_ms(10)

def water_wave(brightness=100, delay=0.1):
    delay = 10
    wave_pattern = [
        [0, 1, 2, 1, 0, 0],
        [1, 2, 3, 2, 1, 0],
        [2, 3, 4, 3, 2, 0],
        [3, 4, 5, 4, 3, 0],
        [4, 5, 6, 5, 4, 0],
        [5, 6, 5, 4, 3, 0],
        [4, 5, 4, 3, 2, 0]
    ]
    
    while True:
        # Forward wave
        for col_offset in range(6):
            led_list_x_y = []
            for row in range(7):
                for col in range(6):
                    adj_col = col + col_offset
                    if adj_col < 6:
                        brightness_value = brightness if wave_pattern[row][col] >= 3 else 0
                        led_list_x_y.append((row, adj_col, brightness_value))
            led_matrix.set_led_list(led_list_x_y)
            time.sleep_ms(delay)
        
        # Backward wave
        for col_offset in range(6, -1, -1):
            led_list_x_y = []
            for row in range(7):
                for col in range(6):
                    adj_col = col + col_offset
                    if adj_col < 6:
                        brightness_value = brightness if wave_pattern[row][col] >= 3 else 0
                        led_list_x_y.append((row, adj_col, brightness_value))
            led_matrix.set_led_list(led_list_x_y)
            time.sleep_ms(delay)
def character_walk(brightness=100, delay=0.5):
    # Define the character in two frames to simulate walking
    character_frame_1 = [
        [0, 0, brightness, brightness, 0, 0],
        [0, brightness, brightness, brightness, brightness, 0],
        [brightness, brightness, brightness, brightness, brightness, brightness],
        [brightness, brightness, 0, 0, brightness, brightness],
        [brightness, brightness, brightness, brightness, brightness, brightness],
        [0, brightness, brightness, brightness, brightness, 0],
        [0, 0, brightness, brightness, 0, 0]
    ]
    
    character_frame_2 = [
        [0, 0, brightness, brightness, 0, 0],
        [0, brightness, brightness, brightness, brightness, 0],
        [brightness, brightness, brightness, brightness, brightness, brightness],
        [brightness, 0, brightness, brightness, 0, brightness],
        [brightness, brightness, brightness, brightness, brightness, brightness],
        [0, brightness, brightness, brightness, brightness, 0],
        [0, brightness, 0, 0, brightness, 0]
    ]

    while True:
        # Display frame 1
        led_list_x_y = []
        for row in range(7):
            for col in range(6):
                brightness_value = character_frame_1[row][col]
                led_list_x_y.append((row, col, brightness_value))
        led_matrix.set_led_list(led_list_x_y)
        time.sleep(delay)
        
        # Display frame 2
        led_list_x_y = []
        for row in range(7):
            for col in range(6):
                brightness_value = character_frame_2[row][col]
                led_list_x_y.append((row, col, brightness_value))
        led_matrix.set_led_list(led_list_x_y)
        time.sleep(delay)

def set_heart_on_led_matrix():
    
    led_list = [(4,0,255)]

    led_matrix.set_led_list(led_list)
# Example animation loop
#while True:
#led_matrix.test_led_matrix()
#led_matrix.test_render_led_map()

#water_wave(100)
character_walk()
    #step_through_leds()
