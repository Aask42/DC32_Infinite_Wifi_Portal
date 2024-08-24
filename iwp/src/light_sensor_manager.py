from LTR_308ALS import LTR_308ALS

class LightSensorManager:
    def __init__(self, i2c):
        self.sensor = LTR_308ALS(i2c)
        self.lux = 0

    def read_sensor(self):
        self.lux = self.sensor.getdata()
        #print(f"Current lux: {self.lux}")
