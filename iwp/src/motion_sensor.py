from lib.LIS2DW12 import LIS2DW12
import utime

class MotionSensor:
    def __init__(self, i2c, motion_threshold=700, debounce_time=0.1):
        self.sensor = LIS2DW12(i2c)
        self.x = 0
        self.y = 0
        self.z = 0
        self.x_motion = False
        self.y_motion = False
        self.z_motion = False
        self.upsidedown = False
        self.x_history = []
        self.y_history = []
        self.z_history = []
        self.motion_threshold = motion_threshold
        self.last_hit_time = 0
        self.debounce_time = debounce_time
        self.previous_jerk_x = 0
        self.previous_jerk_y = 0
        self.previous_jerk_z = 0

    def update_readings(self):
        x = self.sensor.x()
        y = self.sensor.y()
        z = self.sensor.z()
        
        self.x_history.append(x)
        self.y_history.append(y)
        self.z_history.append(z)

        if len(self.x_history) > 10:
            self.x_history.pop(0)
        if len(self.y_history) > 10:
            self.y_history.pop(0)
        if len(self.z_history) > 10:
            self.z_history.pop(0)

        self.x = x
        self.y = y
        self.z = z

        #self.x_motion = self.detect_jerk(self.x_history, 'X')
        #self.y_motion = self.detect_jerk(self.y_history, 'Y')
        self.z_motion = self.detect_jerk(self.z_history, 'Z')

    def detect_jerk(self, history, axis):
        if len(history) < 3:
        #    print(f"[{axis}] Not enough data to calculate jerk")
            return False

        current_time = utime.ticks_ms() / 1000.0
        jerk = self.calculate_jerk(history)

        previous_jerk = self.previous_jerk_x if axis == 'X' else (self.previous_jerk_y if axis == 'Y' else self.previous_jerk_z)
        #print(f"[{axis}] Current value: {history[-1]}, Jerk: {jerk}")

#         if abs(jerk) > self.motion_threshold and previous_jerk * jerk < 0 and (current_time - self.last_hit_time > self.debounce_time):
#             print(f"[{axis}] Current value: {history[-1]}, Jerk: {jerk}")
#             self.last_hit_time = current_time
#             if axis == 'X':
#                 self.previous_jerk_x = jerk
#             elif axis == 'Y':
#                 self.previous_jerk_y = jerk
#             elif axis == 'Z':
#                 self.previous_jerk_z = jerk
#             return True
        
        return False

    def calculate_jerk(self, history):
        # Calculate the velocity change (derivative of acceleration)
        velocity_changes = [history[i] - history[i-1] for i in range(1, len(history))]
        
        # Calculate the jerk (derivative of velocity change)
        if len(velocity_changes) < 2:
            return 0
        jerk = velocity_changes[-1] - velocity_changes[-2]
        return jerk

    def print_motion(self):
        print(f"X,Y,Z: {self.x}, {self.y}, {self.z}")
    
    def print_detected_motion(self):
        if self.x_motion:
            print("X motion detected")
        if self.y_motion:
            print("Y motion detected")
        if self.z_motion:
            print("Z motion detected")
# 
# def update_sensor(timer):
#     sensor.update_readings()
# from machine import Pin, I2C, Timer
# # Initialize I2C and the sensor
# i2c = I2C(1, scl=Pin(22), sda=Pin(21))
# sensor = MotionSensor(i2c)
# 
# # Create and start a timer to update sensor readings every 50ms
# timer = Timer(-1)
# timer.init(period=50, mode=Timer.PERIODIC, callback=update_sensor)
# 
# while True:
#     sensor.print_detected_motion()
#     utime.sleep_ms(10)