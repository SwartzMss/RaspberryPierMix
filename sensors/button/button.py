# -*- coding: utf-8 -*-
"""
Button 按键传感器模块
"""
import lgpio
import time

class ButtonSensor:
    def __init__(self, config):
        self.gpio_chip = int(config.get('gpio_chip', 0))
        self.button_gpio = int(config.get('button_gpio', 17))
        self.h = lgpio.gpiochip_open(self.gpio_chip)
        lgpio.gpio_claim_input(self.h, self.button_gpio, lgpio.SET_PULL_UP)
        self.last_state = 1

    def read(self):
        value = lgpio.gpio_read(self.h, self.button_gpio)
        event = None
        if value == 0 and self.last_state == 1:
            event = {
                'event': 'pressed',
                'timestamp': int(time.time())
            }
        self.last_state = value
        return event

    def get_sensor_info(self):
        return {
            'type': 'button',
            'gpio_chip': self.gpio_chip,
            'button_gpio': self.button_gpio
        } 