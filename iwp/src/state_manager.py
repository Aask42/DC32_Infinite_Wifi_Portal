import uhashlib
import gc

class StateManager:
    def __init__(self):
        self.current_frame_index = 0
        self.frame_index_to_hash = []
        self.frame_hash_table = {}
        self.x_motion = False
        self.y_motion = False
        self.z_motion = False
        self.fading_up = False
        self.fading_down = False
        self.brightness_step = 50  # Default starting brightness
        self.brightness_target = 100  # Default target brightness
        self.matrix_brightness = 100
        self.lux_modifier = 1.0  # Default lux modifier
    
    def set_brightness_led_matrix(self, matrix_brightness=100):
        self.matrix_brightness = matrix_brightness
    
    def get_brightness_led_matrix(self):
        return self.matrix_brightness

    def set_lux_modifier(self, lux_value):
        self.lux_modifier = max(0.0, min(1.0, lux_value / 1000.0))  # Normalize lux value to a range [0, 1]

    def get_lux_modifier(self):
        return self.lux_modifier

    def add_frame(self, frame, delay):
        frame_hash = self._hash_frame(frame)
        if frame_hash not in self.frame_hash_table:
            self.frame_hash_table[frame_hash] = frame
        self.frame_index_to_hash.append((frame_hash, delay))
        gc.collect()

    def get_current_frame(self):
        if self.frame_index_to_hash:
            if self.current_frame_index >= len(self.frame_index_to_hash):
                self.current_frame_index = 0
            frame_hash, delay = self.frame_index_to_hash[self.current_frame_index]
            frame = self.frame_hash_table[frame_hash]
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frame_index_to_hash)
            return frame, delay
        return None, 0

    def set_current_frame(self, frame_num):
        if self.frame_index_to_hash:
            self.current_frame_index = frame_num % len(self.frame_index_to_hash)
        else:
            self.current_frame_index = 0

    def update_motion_state(self, motion_sensor):
        self.x_motion = motion_sensor.x_motion
        self.y_motion = motion_sensor.y_motion
        self.z_motion = motion_sensor.z_motion

    def print_motion_state(self):
        if self.x_motion:
            print("X motion detected")
            self.x_motion = False
        if self.y_motion:
            print("Y motion detected")
            self.y_motion = False
        if self.z_motion:
            print("Z motion detected")
            self.z_motion = False

    def _hash_frame(self, frame):
        frame_bytes = frame.to_bytes(8, 'big')  # Ensure frame is treated as an integer
        return uhashlib.sha256(frame_bytes).digest()[:8]  # 64-bit hash

    def _convert_64bit_to_frame(self, frame_int):
        frame = []
        for x in range(7):
            for y in range(6):
                bit_index = x * 6 + y
                brightness = 255 if (frame_int & (1 << bit_index)) else 0
                frame.append((x, y, brightness))
        return frame