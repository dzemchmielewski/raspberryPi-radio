from threading import Thread
from time import sleep

import gpiozero
from gpiozero import DigitalInputDevice


class Button:
    def __init__(self, pin_number, callback=None):
        self.callback = callback
        self.state = 0
        self.button = gpiozero.Button(pin_number)
        self.button.when_pressed = self.changed
        self.button.when_released = self.changed

    def changed(self):
        if self.button.is_pressed:
            if self.state == 0:
                self.state = 1

        else:  # button is not pressed
            if self.state == 1:
                self.state = 0
                self.callback()


class RotaryButton:
    def __init__(self, pin_number, callback=None):
        self.callback = callback
        self.state = 1
        self.pin = DigitalInputDevice(pin_number, pull_up=None, active_state=True)
        self.pin.when_activated = self.changed
        self.pin.when_deactivated = self.changed

    def changed(self):
        if self.state == 1:
            self.state = 0
        else:  # self.state == 0
            self.state = 1
            self.callback()


class RotaryEncoder:
    DIRECTION_LEFT = 'L'
    DIRECTION_RIGHT = 'R'

    def __init__(self, left_pin_number, right_pin_number, callback=None):
        self.rotor = gpiozero.RotaryEncoder(left_pin_number, right_pin_number, wrap=True)
        self.rotor.when_rotated_clockwise = self.left_changed
        self.rotor.when_rotated_counter_clockwise = self.right_changed
        self.callback = callback

    def left_changed(self):
        self.callback(self.DIRECTION_LEFT)

    def right_changed(self):
        self.callback(self.DIRECTION_RIGHT)


class LED:

    def __init__(self, pin, blinking_time=0.1):
        self.led = gpiozero.LED(pin)
        self.led.off()
        self.stop_blinking = True
        self.blink_thread = None
        self.blinking_time = blinking_time

    def __del__(self):
        if self.blink_thread is not None:
            self.stop_blinking = True
            self.blink_thread.join()

    def __blink__(self):
        self.stop_blinking = False
        while not self.stop_blinking:
            self.led.toggle()
            sleep(self.blinking_time)

    def stop_blink(self):
        if self.blink_thread is not None and self.blink_thread.is_alive():
            self.stop_blinking = True
            self.blink_thread.join()
        self.blink_thread = None

    def start_blink(self):
        if self.blink_thread is None:
            self.blink_thread = Thread(target=self.__blink__)
            self.blink_thread.start()

    def on(self):
        self.stop_blink()
        self.led.on()

    def off(self):
        self.stop_blink()
        self.led.off()
