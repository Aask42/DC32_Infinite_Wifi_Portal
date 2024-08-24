import uasyncio
import math
from matrix_functions.infinity_mirror_font import number_patterns, char_patterns, char_patterns_lower, punctuation_patterns

async def display_number(number, fade_time=0.5, steps=5, led_matrix=None):
    if not led_matrix:
        print("No LED Matrix provided")
        return -1

    rows = led_matrix.rows
    cols = led_matrix.cols

    if number not in number_patterns:
        print(f"Pattern for number {number} not found.")
        return -1

    pattern = number_patterns[number]
    for step in range(steps + 1):
        brightness = int((math.sin(math.pi * step / steps) ** 2) * 100)
        led_list_x_y = []
        for x in range(rows):
            for y in range(cols):
                led_list_x_y.append((x, y, brightness if pattern[x][y] == 1 else 0))
        #print(f"Setting LEDs with brightness: {brightness}")
        led_matrix.set_led_list(led_list_x_y)
        await uasyncio.sleep(fade_time / steps)
    
def get_char_pattern(char):
    if char.isdigit():
        return number_patterns.get(int(char), [[0]*6]*7)
    elif char.isupper():
        return char_patterns.get(char, [[0]*6]*7)
    elif char in punctuation_patterns:
        return punctuation_patterns[char]
    else:
        return char_patterns_lower.get(char, [[0]*6]*7)

async def scroll_text(text="DC32", delay=0.1, led_matrix=None):
    if not led_matrix:
        print("No LED Matrix provided")
        return -1

    led_matrix.clear_matrix()
    buffer = [[0] * (6 * len(text)) for _ in range(7)]
    
    # Create a buffer with all characters side by side
    for i, char in enumerate(text):
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
        led_matrix.set_led_list(led_list)
        await uasyncio.sleep(delay)

def fading_strobe_matrix_frames(max_brightness=100, steps=5, fade_delay=10, rows=7, cols=6):
    frames = []

    # Fade in
    for i in range(steps):
        brightness = int(max_brightness * (i / steps))
        frame = [(x, y, brightness) for x in range(rows) for y in range(cols)]
        frames.append((frame, fade_delay))  # Add frame with delay

    # Brief pause at maximum brightness
    max_brightness_frame = [(x, y, max_brightness) for x in range(rows) for y in range(cols)]
    frames.append((max_brightness_frame, 10))  # Adjust the delay as needed

    # Fade out
    for i in range(steps, 0, -1):
        brightness = int(max_brightness * (i / steps))
        frame = [(x, y, brightness) for x in range(rows) for y in range(cols)]
        frames.append((frame, fade_delay))  # Add frame with delay

    # Turn off all LEDs
    frame = [(x, y, 0) for x in range(rows) for y in range(cols)]
    frames.append((frame, 10))  # Adjust the delay as needed

    return frames

async def fading_strobe_matrix(max_brightness=100, steps=5, fade_delay=10, led_matrix=None):
    if not led_matrix:
        print("No LED Matrix provided")
        return -1

    for i in range(steps):
        brightness = int(max_brightness * (i / steps))
        led_matrix.set_led_list([(x, y, brightness) for x in range(led_matrix.rows) for y in range(led_matrix.cols)])
        await uasyncio.sleep_ms(fade_delay)  # Adjust the delay as needed
    await uasyncio.sleep_ms(10)  # Adjust the delay as needed
    for i in range(steps, 0, -1):
        brightness = int(max_brightness * (i / steps))
        led_matrix.set_led_list([(x, y, brightness) for x in range(led_matrix.rows) for y in range(led_matrix.cols)])
        await uasyncio.sleep_ms(fade_delay)  # Adjust the delay as needed
    led_matrix.set_led_list([(x, y, 0) for x in range(led_matrix.rows) for y in range(led_matrix.cols)])

    await uasyncio.sleep_ms(10)  # Adjust the delay as needed

