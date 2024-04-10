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
        self.state = '11'
        self.direction = None
        self.callback = callback

        self.leftPin = DigitalInputDevice(left_pin_number, pull_up=None, active_state=True)
        self.rightPin = DigitalInputDevice(right_pin_number, pull_up=None, active_state=True)

        self.leftPin.when_activated = self.left_changed
        self.leftPin.when_deactivated = self.left_changed
        self.rightPin.when_activated = self.right_changed
        self.rightPin.when_deactivated = self.right_changed

    def swap(self, char):
        if char == '1':
            return '0'
        else:  # char == '0'
            return '1'

    def left_changed(self):
        self.transition("{}{}".format(self.swap(self.state[0]), self.state[1]))

    def right_changed(self):
        self.transition("{}{}".format(self.state[0], self.swap(self.state[1])))

    def transition(self, new_state):
        if self.state == "11":  # Resting position
            if new_state == "10":  # Turned right 1
                self.direction = "R"
            elif new_state == "01":  # Turned left 1
                self.direction = "L"

        elif self.state == "10":  # R1 or L3 position
            if new_state == "00":  # Turned right 1
                self.direction = "R"
            elif new_state == "11":  # Turned left 1
                if self.direction == "L":
                    if self.callback is not None:
                        self.callback(self.direction)

        elif self.state == "01":  # R3 or L1
            if new_state == "00":  # Turned left 1
                self.direction = "L"
            elif new_state == "11":  # Turned right 1
                if self.direction == "R":
                    if self.callback is not None:
                        self.callback(self.direction)

        else:  # self.state == "00"
            if new_state == "10":  # Turned left 1
                self.direction = "L"
            elif new_state == "01":  # Turned right 1
                self.direction = "R"
            elif new_state == "11":  # Skipped an intermediate 01 or 10 state, but if we know direction then a turn is complete
                if self.direction == "L":
                    if self.callback is not None:
                        self.callback(self.direction)
                elif self.direction == "R":
                    if self.callback is not None:
                        self.callback(self.direction)

        self.state = new_state


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

