
'''
This class is just meant to manage state between timer classes. 
'''
class StateManager():
    def __init__(self):
        self.frame_count = 0
        self.led_matrix_max_brightness = 100
        self.led_ring_max_brightness = 100
        self.current_number = 0
    