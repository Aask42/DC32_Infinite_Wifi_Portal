import time
import uasyncio as asyncio
from micropython import const
from machine import Pin, I2C
from lib.IS31FL3729 import IS31FL3729
import math
import neopixel
from matrix_functions.matrix_setup import set_up_led_matrix

# Configuration
LED_COUNT = 36          # Number of LED pixels.
LED_PIN = 25            # GPIO pin connected to the pixels.
WS_PWR_PIN = 18

p_ws_leds = Pin(WS_PWR_PIN, Pin.OUT)
p_ws_leds.value(1)

# Create the NeoPixel object
led_strip = neopixel.NeoPixel(Pin(LED_PIN), LED_COUNT)

# Initialize the I2C bus and IS31FL3729 driver
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
led_matrix = set_up_led_matrix(i2c)

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

async def make_leds_color(color_hex="770000"):
    r, g, b = hex_to_rgb(color_hex)
    for i in range(LED_COUNT):
        led_strip[i] = (r, g, b)
    
    led_strip.write()  # Update the strip

def calculate_brightness_color(hex_color, brightness):
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    r = int(r * brightness)
    g = int(g * brightness)
    b = int(b * brightness)
    
    return "{:02x}{:02x}{:02x}".format(r, g, b)

base_color_hex = "200110"

async def graphic_eq_with_decay_and_beat(decay_rate=5, beat_interval=500):
    bars = [0] * 6
    max_height = 7
    last_beat_time = time.ticks_ms()

    while True:
        current_time = time.ticks_ms()

        # Simulate new audio input
        new_bars = [min(max_height, int(math.sin(current_time / 1000 + i) * max_height)) for i in range(6)]
        
        # Apply new heights and decay
        for i in range(6):
            if new_bars[i] > bars[i]:
                bars[i] = new_bars[i]
            else:
                bars[i] = max(0, bars[i] - decay_rate)
        
        # Display the bars
        led_list = []
        for x in range(7):
            for y in range(6):
                brightness = 255 if x < bars[y] else 0
                led_list.append((6 - x, y, brightness))  # Reverse x to make it bottom-up
        led_matrix.set_led_list(led_list)
        
        # Fire NeoPixel LEDs on the beat
        if time.ticks_diff(current_time, last_beat_time) >= beat_interval:
            last_beat_time = current_time
            await make_leds_color(base_color_hex)
        else:
            await make_leds_color("000000")
        
        await asyncio.sleep_ms(100)

async def main():
    # Start the graphic equalizer with decay and beat
    await graphic_eq_with_decay_and_beat()

# Run the main function
asyncio.run(main())
