import logging
import time

import board
from adafruit_pca9685 import PCA9685

log = logging.getLogger(__name__)

i2c = board.I2C()

pca = PCA9685(i2c)

current_speed_front_left = 0
current_speed_front_right = 0
current_speed_rear_left = 0
current_speed_rear_right = 0


def init():
    log.info("initialize the PWM module")
    pca.frequency = 50
    pca.channels[0].duty_cycle = 0
    pca.channels[1].duty_cycle = 0
    pca.channels[2].duty_cycle = 0
    pca.channels[3].duty_cycle = 0
    pca.channels[4].duty_cycle = 0
    pca.channels[5].duty_cycle = 0
    pca.channels[6].duty_cycle = 0
    pca.channels[7].duty_cycle = 0


def stop_all():
    pca.channels[0].duty_cycle = 0
    pca.channels[1].duty_cycle = 0
    pca.channels[2].duty_cycle = 0
    pca.channels[3].duty_cycle = 0
    pca.channels[4].duty_cycle = 0
    pca.channels[5].duty_cycle = 0
    pca.channels[6].duty_cycle = 0
    pca.channels[7].duty_cycle = 0
    current_speed_front_left = 0
    current_speed_front_right = 0
    current_speed_rear_left = 0
    current_speed_rear_right = 0


def front_left(speed=0):
    if 0 > abs(speed) > 100:
        log.error(f"speed {speed} outside range 0-100")
        return

    motor_speed = int((abs(speed) * 0xFFFF) / 100)
    current_speed_front_left = speed

    if speed >= 0:
        pca.channels[0].duty_cycle = 0
        pca.channels[1].duty_cycle = motor_speed
    if speed < 0:
        pca.channels[0].duty_cycle = motor_speed
        pca.channels[1].duty_cycle = 0


def rear_left(speed=0):
    if 0 > abs(speed) > 100:
        log.error(f"speed {speed} outside range 0-100")
        return

    motor_speed = int((abs(speed) * 0xFFFF) / 100)
    current_speed_front_right = speed

    if speed >= 0:
        pca.channels[2].duty_cycle = 0
        pca.channels[3].duty_cycle = motor_speed
    if speed < 0:
        pca.channels[2].duty_cycle = motor_speed
        pca.channels[3].duty_cycle = 0


def rear_right(speed=0):
    if 0 > abs(speed) > 100:
        log.error(f"speed {speed} outside range 0-100")
        return

    motor_speed = int((abs(speed) * 0xFFFF) / 100)
    current_speed_rear_left = speed

    if speed >= 0:
        pca.channels[4].duty_cycle = 0
        pca.channels[5].duty_cycle = motor_speed
    if speed < 0:
        pca.channels[4].duty_cycle = motor_speed
        pca.channels[5].duty_cycle = 0


def front_right(speed=0):
    if 0 > abs(speed) > 100:
        log.error(f"speed {speed} outside range 0-100")
        return

    motor_speed = int((abs(speed) * 0xFFFF) / 100)
    current_speed_front_left = speed

    if speed >= 0:
        pca.channels[6].duty_cycle = 0
        pca.channels[7].duty_cycle = motor_speed
    if speed < 0:
        pca.channels[6].duty_cycle = motor_speed
        pca.channels[7].duty_cycle = 0


import logging

from gpiozero import LineSensor

line_sensor_1 = LineSensor(14)
line_sensor_2 = LineSensor(15)
line_sensor_3 = LineSensor(23)


def init_sensors():
    pass


def middle_is_over_black():
    value = line_sensor_2.value
    logging.info(f"middle sensor: {value}")
    return bool(value)


init()
while True:
    if line_sensor_2.value:
        rear_right(15)
        front_left(15)
        rear_left(-15)
        front_right(-15)
        print("Erkannt")
        time.sleep(0.5)
        rear_right(0)
        front_left(0)
        rear_left(0)
        front_right(0)

    elif not line_sensor_2.value:
        print("Nicht Erkannt")
