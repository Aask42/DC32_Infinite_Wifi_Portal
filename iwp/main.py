from machine import I2C, Pin, Timer, deepsleep, reset_cause, DEEPSLEEP_RESET
import gc
import time
import uasyncio as asyncio
from src.ble_sync import BLESync
from src.wifi_manager import WiFiConnection
from src.mqtt_manager import MQTTManager
from CONFIG.MQTT_CONFIG import MQTT_USERNAME, MQTT_PASSWORD, MQTT_CLIENT_ID, MQTT_SERVER
from CONFIG.WIFI_CONFIG import WIFI_LIST
from src.matrix_functions.matrix_manager import MatrixManager
from src.led_controller import LEDController
from src.state_manager import StateManager
from src.animations import AnimationManager
from src.motion_sensor import MotionSensor
from src.light_sensor_manager import LightSensorManager
from src.updates import OTAUpdater
from examples.conways_game import generate_conway_frames
from CONFIG.LED_MANAGER import WS_PWR_PIN, LED_PIN, NUM_LEDS, HUE_INCREMENT, MAX_COLOR_CYCLE

import machine

machine.freq(240000000)

WS_PWR_PIN = 18
p_ws_leds = Pin(WS_PWR_PIN, Pin.OUT)
p_ws_leds.value(1)

# Initialize deep sleep timer
deep_sleep_timer = Timer(12)

def update_display(t, led_matrix, state_manager):
    frame, delay = state_manager.get_current_frame()
    
    if frame:
        led_list = state_manager._convert_64bit_to_frame(frame)
        new_led_list = []
        
        max_brightness = int(state_manager.get_brightness_led_matrix() * state_manager.get_lux_modifier())
        
        for x, y, brightness in led_list:
            if brightness > 0:
                new_led_list.append((x, y, max_brightness))
            else:
                new_led_list.append((x, y, brightness))

        led_matrix.set_led_list(new_led_list)
    gc.collect()

def update_strip(t, led_controller):
    led_controller.update_strip(t)
    gc.collect()

def reset_motion_flag(t):
    motion_sensor_manager.z_motion = False

def enter_deep_sleep():
    print("Entering deep sleep mode...")
    p_ws_leds.value(0)  # Turn off the LEDs
    time.sleep(1)
    p_ws_leds.value(1)

async def fade_brightness(led_controller, state_manager, target_brightness, duration):
    initial_brightness = led_controller.get_brightness()
    step_count = 50  # Number of steps in the fade transition
    step_duration = duration / step_count
    brightness_step = (target_brightness - initial_brightness) / step_count
    
    for step in range(step_count):
        current_brightness = initial_brightness + step * brightness_step
        led_controller.set_brightness(current_brightness)
        state_manager.set_brightness_led_matrix(current_brightness)
        await asyncio.sleep(step_duration)

async def handle_upsidedown(motion_sensor_manager, led_controller, state_manager):
    await fade_brightness(led_controller, state_manager, 1, 2)  # 2 seconds to transition to full brightness
    await asyncio.sleep(10)  # Wait for 10 seconds while upside down
    if motion_sensor_manager.upsidedown:
        print("Upside down for more than 10 seconds. Turning off LEDs.")
        led_controller.set_brightness(0)
        state_manager.set_brightness_led_matrix(0)

def sensor_timer_callback(t, motion_sensor_manager, state_manager, led_controller):
    motion_sensor_manager.update_readings()
    state_manager.update_motion_state(motion_sensor_manager)
    
    z_value = motion_sensor_manager.z_history[-1]
    #print(f"Z-axis value: {z_value}")

    if z_value < -700 and not motion_sensor_manager.upsidedown:
        motion_sensor_manager.upsidedown = True
        print("I'm upside down!")
        asyncio.create_task(handle_upsidedown(motion_sensor_manager, led_controller, state_manager))

    if z_value > -400 and motion_sensor_manager.upsidedown:
        motion_sensor_manager.upsidedown = False
        print("I'm right side up!")
        asyncio.create_task(fade_brightness(led_controller, state_manager, 100, 2))  # 2 seconds to transition to full brightness

def trigger_on_beat(t, led_controller):
    led_controller.update_direction()

def ble_timer_callback(t, ble_sync):
    ble_sync.sync_frames(t)
    gc.collect()

async def ota_update_kickoff(filename):
    updater = OTAUpdater(f"{filename}")
    await updater.update_file_replace()

def sub_cb(topic, msg, direction_timer, display_timer, state_manager, led_controller, led_matrix, matrix_manager):
    msg_string = msg.decode("UTF-8")
    print(f"Received message: {msg} on topic: {topic.decode()} ")
    if topic == b'bpm':
        state_manager.current_frame_index = 0
        led_controller.cycle = 0
        bpm = int(int(msg_string) * 1.00)
        direction_timer.init(period=int(60000 / bpm), mode=Timer.PERIODIC, callback=lambda t: trigger_on_beat(t, led_controller))
        display_timer.init(freq=int(bpm/4), mode=Timer.PERIODIC, callback=lambda t: update_display(t, led_matrix, state_manager))
    if topic == b'banner':
        frame_generator = matrix_manager.scroll_text_frames(f"{msg_string}", delay=0.05)
        state_manager.frame_index_to_hash = []
        for frame, delay in frame_generator:
            state_manager.add_frame(frame, delay)
    if topic == b'update':
        print("I should update....")
        asyncio.create_task(ota_update_kickoff(msg_string))

async def schedule_update(msg_string):
    updater = OTAUpdater(f"{msg_string}")
    await updater.update_file_replace()

async def read_light_sensor(light_sensor_manager, state_manager):
    """Coroutine to read light sensor periodically."""
    while True:
        lux = light_sensor_manager.read_sensor()  # Measure lux
        if lux is not None:  # Ensure valid lux reading
            state_manager.set_lux_modifier(lux)
        await asyncio.sleep(1)  # Adjust the delay as needed

def set_led_length(t, led_controller, wifi_manager):
    led_controller.num_leds_lit = wifi_manager.network_count
    

async def main():
    gc.enable()
    led_controller = LEDController(NUM_LEDS, LED_PIN, 50, HUE_INCREMENT, MAX_COLOR_CYCLE)

    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
    state_manager = StateManager()
    matrix_manager = MatrixManager(state_manager, i2c)
    
    motion_sensor_manager = MotionSensor(i2c=i2c)
    motion_sensor_manager_timer = Timer(4)
    motion_sensor_manager_timer.init(freq=7, mode=Timer.PERIODIC, callback=lambda t: sensor_timer_callback(t, motion_sensor_manager, state_manager, led_controller))

    # Initialize timers and other components
    frame_generator = matrix_manager.scroll_text_frames("_DC32_2024_")
    for frame, delay in frame_generator:
        state_manager.add_frame(frame, delay)

    frame_timer = Timer(1)
    frame_timer.init(freq=15, mode=Timer.PERIODIC, callback=lambda t: update_strip(t, led_controller))

    display_timer = Timer(2)
    display_timer.init(freq=15, mode=Timer.PERIODIC, callback=lambda t: update_display(t, matrix_manager.led_matrix, state_manager))

    direction_timer = Timer(3)
    bpm = 85
    direction_timer.init(period=int(60000 / bpm), mode=Timer.PERIODIC, callback=lambda t: trigger_on_beat(t, led_controller))

    # Initialize WiFi and MQTT managers
    # Comment this section if you don't want wireless features
    if "YOURWIFINETWORK" != WIFI_LIST[0][0]:
        wifi_count_timer = Timer(16)
        wifi_count_timer.init(period=int(60000 / 30), mode=Timer.PERIODIC, callback=lambda t: set_led_length(t, led_controller, wifi_manager))

        wifi_manager = WiFiConnection()
        await wifi_manager.main()
        if MQTT_USERNAME != b"YOURUSERNAME":
            mqtt_manager = MQTTManager(MQTT_SERVER, MQTT_CLIENT_ID, MQTT_USERNAME, MQTT_PASSWORD)
            await mqtt_manager.main(wifi_manager)  # Ensure the MQTT waits for WiFi connection
            mqtt_manager.set_callback(lambda topic, msg: sub_cb(topic, msg, direction_timer, display_timer, state_manager, led_controller, matrix_manager.led_matrix, matrix_manager))

            await mqtt_manager.subscribe(b'bpm')
            await mqtt_manager.subscribe(b'banner')
            #await mqtt_manager.subscribe(b'update')
        else:
            print("Please configure your MQTT server to control over the internet")
    else:
        print("Please configure your WIFI to connect to the internet")
        asyncio.create_task(wifi_manager.update_network_count())

    # Initialize Light Sensor Manager
    light_sensor_manager = LightSensorManager(i2c)
    asyncio.create_task(read_light_sensor(light_sensor_manager, state_manager))

    while True:
        await asyncio.sleep(1)
        gc.collect()

asyncio.run(main())



