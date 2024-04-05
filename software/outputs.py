#!/usr/bin/python
from threading import Thread
from time import sleep

import vlc

from bus import Bus
from entities import TunerStatus, RadioItem, TUNER_OUTPUT_LOG, LED_OUTPUT_LOG
from gpiozero import LED
from configuration import LED_TUNER_STATUS


class Tuner(RadioItem):
    CODE = "tuner"
    EVENT_STATION = "station"
    EVENT_PLAY_STATUS = "status"

    def __init__(self):
        super(Tuner, self).__init__(Bus(TUNER_OUTPUT_LOG, Tuner.CODE))
        self.player = vlc.MediaPlayer()
        self.is_playing = False

    def __del__(self):
        self.player.stop()

    def status(self):
        if self.is_playing:
            return TunerStatus.PLAYING
        return TunerStatus.TUNING

    def loop(self):
        if (station := self.bus.consume_event(Tuner.EVENT_STATION)) is not None:
            # First notify about the sound break:
            self.is_playing = False
            self.bus.send_manager_event(Tuner.EVENT_PLAY_STATUS, self.status())
            # Then change the station:
            # self.bus.log("Playing " + str(station))
            self.player.set_media(vlc.Media(station.url))
            self.player.play()
        else:
            current_playing_status = self.player.is_playing()
            if self.is_playing != current_playing_status:
                self.is_playing = current_playing_status
                self.bus.send_manager_event(Tuner.EVENT_PLAY_STATUS, self.status())


class LEDOutput(RadioItem):
    CODE = "led"
    EVENT_STATUS = "status"

    def __init__(self):
        super(LEDOutput, self).__init__(Bus(LED_OUTPUT_LOG, LEDOutput.CODE))
        self.led = LED(LED_TUNER_STATUS)
        self.led.off()
        self.stop_blinking = True
        self.blink_thread = None

    def __del__(self):
        if self.blink_thread is not None:
            self.stop_blinking = True
            self.blink_thread.join()

    def blink(self):
        self.stop_blinking = False
        while not self.stop_blinking:
            self.led.toggle()
            sleep(0.1)

    def stop_blink(self):
        if self.blink_thread is not None and self.blink_thread.is_alive():
            self.stop_blinking = True
            self.blink_thread.join()
        self.blink_thread = None

    def start_blink(self):
        if self.blink_thread is None:
            self.blink_thread = Thread(target=self.blink)
            self.blink_thread.start()

    def loop(self):
        if (event := self.bus.consume_event(LEDOutput.EVENT_STATUS)) is not None:

            if event.status == TunerStatus.PLAYING:
                self.stop_blink()
                self.led.on()

            elif event.status == TunerStatus.TUNING:
                self.start_blink()

            else:
                self.stop_blink()
                self.led.off()
