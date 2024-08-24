import neopixel
from machine import Pin, Timer
from src.helpers import hsv_to_rgb  # Import the helper function

try:
    from CONFIG.LED_MANAGER import MAX_BRIGHTNESS
except:
    print("You didn't provide a max brightness, setting to 100 to not blind you")
    MAX_BRIGHTNESS = 100

class LEDController:
    def __init__(self, num_pixels, pin_num, brightness, hue_increment, max_color_cycle, max_brightness=MAX_BRIGHTNESS):
        self.num_pixels = num_pixels
        self.np = neopixel.NeoPixel(Pin(pin_num), num_pixels)
        self.brightness = brightness
        self.hue_increment = hue_increment
        self.max_color_cycle = max_color_cycle
        self.max_brightness = max_brightness  # Add max_brightness
        self.position = 0
        self.cycle = 0
        self.direction = 1
        self.frame_count = 0
        self.current_number = 0
        self.timer = Timer(-1)
        self.brightness_step = 0
        self.target_brightness = brightness
        self.num_leds_lit = self.num_pixels/3 * 2

    def get_brightness(self):
        return self.max_brightness
    def set_brightness(self, max_brightness=100):
        self.max_brightness = max_brightness
    
    def update_direction(self):
        self.direction *= -1  # Change direction properly

    def update_position(self):
        self.position = (self.position + self.direction) % self.num_pixels

    def generate_frame(self):
        self.np.fill((0, 0, 0))  # Clear all pixels
        base_hue = (self.cycle / self.max_color_cycle) % 1
        for offset in range(self.num_leds_lit):
            current_hue = (base_hue + offset * self.hue_increment) % 1
            color = hsv_to_rgb(current_hue, 1, self.brightness / 255 * self.max_brightness / 255)  # Adjust brightness scale
            idx = (self.position + offset) % self.num_pixels
            self.np[idx] = color  # Directly set the color in the NeoPixel buffer
        return self.np

    def display_frame(self):
        self.np.write()
        self.frame_count += 1

    def update_strip(self, t):
        self.generate_frame()
        self.display_frame()
        self.update_position()
        self.cycle = (self.cycle + self.direction) % self.max_color_cycle
        if self.cycle < 0:
            self.cycle = self.max_color_cycle - 1

    def set_brightness(self, brightness):
        self.brightness = min(brightness, self.max_brightness)  # Ensure brightness does not exceed max_brightness

    def smooth_brightness_transition(self, target_brightness, duration_ms=75):
        self.target_brightness = min(target_brightness, self.max_brightness)
        step_duration = 10  # ms
        steps = max(duration_ms // step_duration, 1)
        self.brightness_step = (self.target_brightness - self.brightness) / steps
        self.timer.init(period=step_duration, mode=Timer.PERIODIC, callback=self._adjust_brightness)

    def _adjust_brightness(self, timer):
        if (self.brightness_step > 0 and self.brightness >= self.target_brightness) or \
           (self.brightness_step < 0 and self.brightness <= self.target_brightness):
            self.brightness = self.target_brightness
            self.timer.deinit()
        else:
            self.brightness += self.brightness_step
            # Clamp the brightness to ensure it doesn't exceed bounds due to floating point precision issues
            self.brightness = max(0, min(self.brightness, self.max_brightness))
        self.update_strip(None)  # Update the LED strip with the new brightness

# Example usage
# controller = LEDController(num_pixels=30, pin_num=2, brightness=50, hue_increment=0.02, max_color_cycle=100)
# controller.smooth_brightness_transition(target_brightness=100, duration_ms=75)

