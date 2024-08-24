from lib.IS31FL3729 import IS31FL3729
from machine import Pin, I2C
import uasyncio as asyncio
import framebuf
import math
from src.matrix_functions.infinity_mirror_font import number_patterns, char_patterns, char_patterns_lower, punctuation_patterns
import gc

class MatrixManager:
    def __init__(self, state_manager, i2c=None):
        self.state_manager = state_manager
        self.i2c = i2c if i2c else I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
        self.led_matrix = IS31FL3729(self.i2c)
        self._setup_led_matrix()

    def _setup_led_matrix(self):
        cs_currents = [0x40] * 14
        cs_currents.append(0xff)
        self.led_matrix.cs_currents = cs_currents
        self._create_led_matrix_map()
        self._create_led_brightness_map()
        self.led_matrix.rows = 7
        self.led_matrix.cols = 6
        self.led_matrix.start_display()

    def refresh(self):
        self.led_matrix.render_led_map()
        gc.collect()

    def _create_led_matrix_map(self):
        self.led_matrix.led_matrix_map = {
            (0, 0): 0x2e, (0, 1): 0x2d, (0, 2): 0x1e, (0, 3): 0x1d, (0, 4): 0x0e, (0, 5): 0x0d, (0, 6): 0x1f,
            (1, 0): 0x2c, (1, 1): 0x2b, (1, 2): 0x1c, (1, 3): 0x1b, (1, 4): 0x0c, (1, 5): 0x0b, (1, 6): 0x0f,
            (2, 0): 0x2a, (2, 1): 0x29, (2, 2): 0x1a, (2, 3): 0x19, (2, 4): 0x0a, (2, 5): 0x09,
            (3, 0): 0x28, (3, 1): 0x27, (3, 2): 0x18, (3, 3): 0x17, (3, 4): 0x08, (3, 5): 0x07,
            (4, 0): 0x26, (4, 1): 0x25, (4, 2): 0x16, (4, 3): 0x15, (4, 4): 0x06, (4, 5): 0x05,
            (5, 0): 0x24, (5, 1): 0x23, (5, 2): 0x14, (5, 3): 0x13, (5, 4): 0x04, (5, 5): 0x03,
            (6, 0): 0x22, (6, 1): 0x21, (6, 2): 0x12, (6, 3): 0x11, (6, 4): 0x02, (6, 5): 0x01
        }

    def _create_led_brightness_map(self):
        self.led_matrix.led_brightness_map = {i: 0 for i in range(0x30)}

    def test_turn_on_all(self, brightness=100):
        for x in range(7):
            for y in range(6):
                address = self.led_matrix.led_matrix_map[(x, y)]
                self.led_matrix.led_brightness_map[address] = brightness
        self.refresh()

    async def display_number(self, number, fade_time=0.5, steps=5):
        if number not in number_patterns:
            print(f"Pattern for number {number} not found.")
            return -1

        pattern = number_patterns[number]
        for step in range(steps + 1):
            brightness = int((math.sin(math.pi * step / steps) ** 2) * 100)
            buffer = self._create_buffer_from_pattern(pattern, brightness)
            self.led_matrix.set_led_list(buffer)
            await asyncio.sleep(fade_time / steps)
        gc.collect()

    def get_char_pattern(self, char):
        if char.isdigit():
            return number_patterns.get(int(char), [[0]*6]*7)
        elif char.isupper():
            return char_patterns.get(char, [[0]*6]*7)
        elif char in punctuation_patterns:
            return punctuation_patterns[char]
        else:
            return char_patterns_lower.get(char, [[0]*6]*7)

    def scroll_text_frames(self, text="DC32", delay=0.1):
        """Generate frames to scroll the text across the display.
        
        Args:
            text (str): The text to scroll.
            delay (float): Delay between frames in seconds.

        Yields:
            Tuple[int, float]: Frame buffer as integer and delay.
        """
        text = text.lstrip()
        buffer_width = 7 * len(text)  # Each character is 6 pixels wide + 1 blank column
        buffer = framebuf.FrameBuffer(bytearray(buffer_width * self.led_matrix.rows), buffer_width, self.led_matrix.rows, framebuf.MONO_HLSB)

        # Draw characters onto the buffer
        for i, char in enumerate(text):
            pattern = self.get_char_pattern(char)
            for x in range(self.led_matrix.rows):
                for y in range(6):
                    buffer.pixel(i * 7 + y, x, pattern[x][y])

            # Add blank column after each character
            for x in range(self.led_matrix.rows):
                buffer.pixel(i * 7 + 6, x, 0)

        # Scroll text off the display
        total_frames = buffer_width + self.led_matrix.cols  # Scroll completely off the display
        for offset in range(total_frames):
            frame_int = self._create_buffer_from_framebuffer(buffer, offset)
            yield frame_int, delay

    async def scroll_text(self, text="DC32", delay=0.1):
        frame_generator = self.scroll_text_frames(text, delay)
        for frame, frame_delay in frame_generator:
            led_list = self._convert_64bit_to_frame(frame)
            self.led_matrix.set_led_list(led_list)
            await asyncio.sleep(frame_delay)
        gc.collect()

    def generate_sine_wave(self, frames, frequency=1, amplitude=3):
        wave = []

        for frame in range(frames):
            matrix = [[0] * 7 for _ in range(6)]  # Initialize a 6x7 matrix

            for x in range(6):
                y = int(amplitude * math.sin(2 * math.pi * frequency * (frame + x) / frames) + amplitude)
                if y < 7:
                    matrix[x][y] = 1  # Assign the sine wave value

            # Rotate the matrix 90 degrees clockwise
            rotated_matrix = [[0] * 6 for _ in range(7)]
            for x in range(6):
                for y in range(7):
                    rotated_matrix[y][5 - x] = matrix[x][y]

            frame_int = self._convert_frame_to_64bit(self._create_buffer_from_pattern(rotated_matrix, 255))
            wave.append((frame_int, 0.05))

        return wave

    def fading_strobe_matrix_frames(self, max_brightness=100, steps=5, fade_delay=10):
        for i in range(steps):
            brightness = int(max_brightness * (i / steps))
            frame_int = self._create_buffer_from_brightness(brightness)
            yield frame_int, fade_delay
        max_brightness_frame = self._create_buffer_from_brightness(max_brightness)
        yield max_brightness_frame, 10
        for i in range(steps, 0, -1):
            brightness = int(max_brightness * (i / steps))
            frame_int = self._create_buffer_from_brightness(brightness)
            yield frame_int, fade_delay
        frame_int = self._create_buffer_from_brightness(0)
        yield frame_int, 10

    async def fading_strobe_matrix(self, max_brightness=100, steps=5, fade_delay=10):
        frame_generator = self.fading_strobe_matrix_frames(max_brightness, steps, fade_delay)
        for frame, frame_delay in frame_generator:
            led_list = self._convert_64bit_to_frame(frame)
            self.led_matrix.set_led_list(led_list)
            await asyncio.sleep_ms(frame_delay)
        gc.collect()

    def _convert_frame_to_64bit(self, frame):
        frame_int = 0
        for x, y, brightness in frame:
            bit_index = x * self.led_matrix.cols + y
            frame_int |= (brightness > 0) << bit_index
        return frame_int

    def _convert_64bit_to_frame(self, frame_int):
        frame = []
        for x in range(self.led_matrix.rows):
            for y in range(self.led_matrix.cols):
                bit_index = x * self.led_matrix.cols + y
                brightness = 255 if (frame_int & (1 << bit_index)) else 0
                frame.append((x, y, brightness))
        return frame

    def _create_buffer_from_pattern(self, pattern, brightness):
        buffer = []
        for x in range(self.led_matrix.rows):
            for y in range(self.led_matrix.cols):
                if pattern[x][y] == 1:
                    buffer.append((x, y, brightness))
                else:
                    buffer.append((x, y, 0))
        return buffer

    def _create_buffer_from_framebuffer(self, buffer, offset):
        frame_int = 0
        for x in range(self.led_matrix.rows):
            for y in range(self.led_matrix.cols):
                bit_index = x * self.led_matrix.cols + y
                brightness = 255 if buffer.pixel(y + offset, x) == 1 else 0
                frame_int |= (brightness > 0) << bit_index
        return frame_int

    def _create_buffer_from_brightness(self, brightness):
        frame_int = 0
        for x in range(self.led_matrix.rows):
            for y in range(self.led_matrix.cols):
                bit_index = x * self.led_matrix.cols + y
                frame_int |= (brightness > 0) << bit_index
        return frame_int
