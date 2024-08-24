import time
import uasyncio as asyncio
from machine import Pin, I2C
from lib.IS31FL3729 import IS31FL3729

from src.matrix_functions.infinity_mirror_font import char_patterns, char_patterns_lower
from src.matrix_functions.matrix_setup import set_up_led_matrix

# Initialize the I2C bus and IS31FL3729 driver
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
display = set_up_led_matrix(i2c=i2c)

def get_char_pattern(char):
    if char.isupper():
        return char_patterns.get(char, [[0]*6]*7)
    else:
        return char_patterns_lower.get(char, [[0]*6]*7)

async def scroll_text(name, delay=0.1):
    display.clear_matrix()
    buffer = [[0] * (6 * len(name)) for _ in range(7)]
    
    # Create a buffer with all characters side by side
    for i, char in enumerate(name):
        pattern = get_char_pattern(char)
        for x in range(7):
            for y in range(6):
                buffer[x][i*6 + y] = pattern[x][y]

    # Scroll the buffer
    for offset in range(len(buffer[0]) - 6 + 1):
        led_list = []
        for x in range(7):
            for y in range(6):
                brightness = 255 if buffer[x][y + offset] == 1 else 0
                led_list.append((x, y, brightness))
        display.set_led_list(led_list)
        await asyncio.sleep(delay)

async def main():
    while True:
        await scroll_text("    THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG     the quick brown fox jumps over the lazy dog", delay=0.04)

# Run the main function
asyncio.run(main())
