import random
import math
import gc

class AnimationManager:
    def __init__(self):
        self.animations = {
            "jump_man": self.jump_man_frames,
            "wave": self.wave,
            "cat": self.cat,
            "flashy": self.flashy,
            "heart": self.heart,
        }
    def generate_motion_frames(self, x_history, y_history, z_history, duration=0.5):
        frames = []
        
        # Ensure there is at least one historical coordinate to start from
        if not x_history or not y_history or not z_history:
            return frames

        # Get the latest coordinates
        x = x_history[-1]
        y = y_history[-1]
        z = z_history[-1]

        # Create initial frame
        frame = [[0] * 6 for _ in range(7)]
        for pixel in frame:
            pixel = 1
        #frame[x % 7][y % 6] = 1  # Place the ball at the initial position

        frames.append((frame, duration))

        # Iterate over historical coordinates to generate motion frames
        for i in range(len(x_history) - 1):
            frame = [[0] * 6 for _ in range(7)]
            x = x_history[i]
            y = y_history[i]
            z = z_history[i]
            
            frame[x % 7][y % 6] = 1  # Update the ball position based on history
            frames.append((frame, duration))

        return frames
    def strobe_matrix(self, steps = 10):
        frames = []
        for i in range(steps):
            frame = []
            brightness = int(100 * (i / steps))
            for x in range(7):
                for y in range(6):
                    frame.append([x, y, brightness])
            frames.append(frame)
        #await uasyncio.sleep_ms(10)  # Adjust the delay as needed
        for i in range(steps, 0, -1):
            frame = []
            brightness = int(100 * (i / steps))
            for x in range(7):
                for y in range(6):
                    frame.append([x, y, brightness])
            frames.append(frame)
        return frames
    def convert_to_matrix_map(self, frames_list):
        gc.collect()
        list_of_mod_frames = []
        for frame, delay in frames_list:
            temp_frame = []
            rows = len(frame)
            for x in range(rows):
                cols = len(frame[x])
                for y in range(cols):
                    if frame[x][y] == 1:
                        brightness = 50
                    else:
                        brightness = 0
                    temp_frame.append((x, y, brightness))
            list_of_mod_frames.append((temp_frame, delay))
        return list_of_mod_frames

    def generate_eq_frames(self, num_frames):
        rows = 7
        columns = 6
        frames = []
        
        for frame_number in range(num_frames):
            new_frame = []
            
            levels = [random.randint(0, rows) for _ in range(columns)]
            peak_levels = [min(level + random.randint(0, 1), rows) for level in levels]

            for x in range(columns):
                for y in range(rows):
                    if y < levels[x]:
                        new_frame.append((y, x, 50))  # Brightness is 255 for ON
                    else:
                        new_frame.append((y, x, 0))    # Brightness is 0 for OFF
            
            # Draw peak level
            for x in range(columns):
                peak_level_int = peak_levels[x]
                if peak_level_int > 0:
                    new_frame.append((rows - peak_level_int, x, 50))  # Brightness is 255 for peak

            frames.append((new_frame, 0.5))

        return frames


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

            wave.append((rotated_matrix, 0.05))  # Use a duration of 0.1 seconds for each frame

        return wave


    def spiral_and_wipe(self, delay=0):
        rows, cols = 7, 7

        def is_valid_position(x, y):
            if x < 2:
                return 0 <= x < rows and 0 <= y < 7
            else:
                return 0 <= x < rows and 0 <= y < 6

        def generate_spiral():
            layer = 0
            step = 0
            while layer < (min(rows, cols) // 2):
                # Top row (left to right)
                for col in range(layer, cols - layer):
                    if is_valid_position(layer, col):
                        brightness = 50 + 50 * (step % 2)  # Vary brightness between 50 and 100
                        yield [(layer, col, brightness)], delay
                        step += 1
                # Right column (top to bottom)
                for row in range(layer + 1, rows - layer):
                    if is_valid_position(row, cols - layer - 1):
                        brightness = 50 + 50 * (step % 2)  # Vary brightness between 50 and 100
                        yield [(row, cols - layer - 1, brightness)], delay
                        step += 1
                # Bottom row (right to left)
                for col in range(cols - layer - 2, layer - 1, -1):
                    if is_valid_position(rows - layer - 1, col):
                        brightness = 50 + 50 * (step % 2)  # Vary brightness between 50 and 100
                        yield [(rows - layer - 1, col, brightness)], delay
                        step += 1
                # Left column (bottom to top)
                for row in range(rows - layer - 2, layer, -1):
                    if is_valid_position(row, layer):
                        brightness = 50 + 50 * (step % 2)  # Vary brightness between 50 and 100
                        yield [(row, layer, brightness)], delay
                        step += 1
                layer += 1

        def generate_wipe(frames):
            for frame in frames:
                x, y, brightness = frame[0][0]
                yield [(x, y, 0)], delay

        # Generate spiral in
        spiral_frames = list(generate_spiral())

        # Generate wipe off
        wipe_frames = list(generate_wipe(spiral_frames))

        return wipe_frames + spiral_frames

    def pulse_brightness(self, frames, pulse_factor):
        pulsed_frames = []
        for frame, delay in frames:
            pulsed_frame = [(x, y, min(100, brightness * pulse_factor)) for (x, y, brightness) in frame]
            pulsed_frames.append((pulsed_frame, delay))
        return pulsed_frames

    def trigger_on_beat(self, t, state_manager, led_controller):
        # Pulse the brightness of currently lit pixels
        current_frames = state_manager.frames[state_manager.current_frame_index:]
        # pulsed_frames = pulse_brightness(current_frames, 2)  # Pulse factor can be adjusted
        # state_manager.add_frames(pulsed_frames)
        led_controller.update_direction()  # Change LED ring direction on beat

    @property
    def jump_man_frames(self):
        return [
            ([
                [0, 0, 1, 0, 0, 0],
                [0, 1, 1, 1, 0, 0],
                [0, 0, 1, 0, 0, 0],
                [0, 1, 1, 1, 0, 0],
                [1, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 0],
                [1, 0, 0, 0, 0, 1],
            ], 0.5),
            ([
                [0, 0, 1, 0, 0, 0, 1],
                [0, 1, 1, 1, 0, 0],
                [0, 0, 1, 0, 0, 0],
                [0, 1, 1, 1, 0, 0],
                [0, 1, 0, 1, 0, 0],
                [0, 0, 1, 0, 0, 0],
                [1, 0, 0, 0, 1, 0],
            ], 0.75),
            ([
                [0, 0, 1, 0, 0, 0, 1],
                [0, 1, 1, 1, 0, 0, 1],
                [0, 0, 1, 0, 0, 0],
                [0, 1, 1, 1, 0, 0],
                [0, 0, 1, 0, 0, 0],
                [0, 1, 0, 1, 0, 0],
                [1, 0, 0, 0, 0, 1],
            ], 0.75),
            ([
                [0, 0, 1, 0, 0, 0, 0],
                [0, 1, 1, 1, 0, 0, 1],
                [0, 0, 1, 0, 0, 0],
                [0, 1, 1, 1, 0, 0],
                [1, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 0],
                [0, 0, 1, 0, 1, 0],
            ], 0.5)
        ]

    @property
    def wave(self):
        return [
            ([
                [1, 0, 0, 0, 1, 0, 0],
                [0, 1, 0, 1, 0, 0, 0],
                [0, 0, 1, 0, 0, 0],
                [0, 1, 0, 1, 0, 0],
                [1, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 0],
            ], 0.5),
            
            ([
                
                [0, 1, 0, 1, 0, 0, 0],
                [0, 0, 1, 0, 0, 0, 0],
                [0, 1, 0, 1, 0, 0],
                [1, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 0],
                [1, 0, 0, 0, 1, 0],
            ], 0.5),
            
            ([ 
                [0, 0, 1, 0, 0, 0, 0],
                [0, 1, 0, 1, 0, 0, 0],
                [1, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 0],
                [1, 0, 0, 0, 1, 0],
                [0, 1, 0, 1, 0, 0],
            ], 0.5),
                ([ 
                [0, 1, 0, 1, 0, 0,0],
                [1, 0, 0, 0, 1, 0,1],
                [0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 0],
                [1, 0, 0, 0, 1, 0],
                [0, 1, 0, 1, 0, 0],
                [0, 0, 1, 0, 0, 0],
            ], 0.5),
            ([ 
                [1, 0, 0, 0, 1, 0, 1],
                [0, 0, 0, 0, 0, 1, 1],
                [0, 0, 0, 0, 0, 0],
                [1, 0, 0, 0, 1, 0],
                [0, 1, 0, 1, 0, 0],
                [0, 0, 1, 0, 0, 0], 
                [0, 1, 0, 1, 0, 0],
            ], 0.5),
            ([ 
                [0, 0, 0, 0, 0, 1, 1],
                [0, 0, 0, 0, 0, 0, 0],
                [1, 0, 0, 0, 1, 0],
                [0, 1, 0, 1, 0, 0],
                [0, 0, 1, 0, 0, 0],
                [0, 1, 0, 1, 0, 0],
                [1, 0, 0, 0, 1, 0],

            ], 0.5),
                ([ 
                [0, 0, 0, 0, 0, 0, 0],
                [1, 0, 0, 0, 1, 0, 0],
                [0, 1, 0, 1, 0, 0],
                [0, 0, 1, 0, 0, 0],
                [0, 1, 0, 1, 0, 0],
                [1, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 1],

            ], 0.5),
        ]

    @property
    def cat(self):
        return [([
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 1],
            [0, 0, 1, 1, 1, 1],
            [0, 0, 0, 0, 1, 1],
            [0, 0, 0, 1, 0, 1],
            [0, 0, 0, 1, 0, 1],
        ], 0.5),

        ([
            [0, 1, 0, 0, 0, 0, 0],
            [0, 1, 1, 0, 1, 1, 0],
            [0, 0, 1, 1, 1, 1],
            [0, 0, 1, 1, 1, 1],
            [0, 0, 1, 0, 1, 1],
            [0, 0, 1, 0, 0, 1],
            [0, 0, 0, 0, 0, 1],
        ], 0.5),]

    @property
    def flashy(self):
        return [([
            [1, 0, 1, 0, 1, 0, 1],
            [0, 1, 0, 1, 0, 1, 0],
            [1, 0, 1, 0, 1, 0],
            [0, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 0],
            [0, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 0],
        ], 0.5),

        ([
            [0, 1, 0, 1, 0, 1, 0],
            [1, 0, 1, 0, 1, 0, 1],
            [0, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 0],
            [0, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 0],
            [0, 1, 0, 1, 0, 1],
        ], 0.5),]

    @property
    def heart(self):
        return [([
            [0, 1, 0, 0, 1, 0, 1],
            [1, 0, 1, 1, 0, 1, 0],
            [1, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 1],
            [0, 1, 0, 0, 1, 0],
            [0, 0, 1, 1, 0, 0],
        ], 2.00),

        ([
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 0, 1],
            [0, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ], 2.00),]

