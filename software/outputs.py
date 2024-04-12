#!/usr/bin/python
from datetime import datetime, timedelta
from urllib.request import urlopen

import vlc

from bus import Bus
from configuration import FULL_LOAD
from entities import TunerStatus, RadioItem, TUNER_OUTPUT_LOG, LED_OUTPUT_LOG, DISPLAY_OUTPUT_LOG
from oled.display_manager import DisplayManager

if FULL_LOAD:
    from hardware import LED
    from oled.lib import OLED_1in32

from oled.picture_creator import PictureCreator


class Tuner(RadioItem):
    CODE = "tuner"
    EVENT_STATION = "station"
    EVENT_PLAY_STATUS = "status"
    EVENT_RECORD = "record"

    def __init__(self):
        super(Tuner, self).__init__(Bus(TUNER_OUTPUT_LOG, Tuner.CODE))
        self.player = vlc.MediaPlayer()
        self.is_playing = False
        self.current_station = None
        self.recording = 0

    def exit(self):
        self.player.stop()

    def status(self):
        if self.is_playing:
            return TunerStatus.PLAYING
        return TunerStatus.TUNING

    @staticmethod
    def record(filepath, stream, duration):
        fd = open(filepath, 'wb')
        begin = datetime.now()
        duration = timedelta(milliseconds=duration)
        while datetime.now() - begin < duration:
            data = stream.read(10000)
            fd.write(data)
        fd.close()

    def loop(self):
        if (station := self.bus.consume_event(Tuner.EVENT_STATION)) is not None:
            # First notify about the sound break:
            self.is_playing = False
            self.bus.send_manager_event(Tuner.EVENT_PLAY_STATUS, self.status())
            # Then change the station:
            # self.bus.log("Playing " + str(station))
            self.current_station = station
            self.player.set_media(vlc.Media(station.url))
            self.player.play()
        elif (event := self.bus.consume_event(Tuner.EVENT_RECORD)) is not None:
            # TODO: thread this part
            Tuner.record('handtests/clip.mp3', urlopen(self.current_station.url), 5000)
        else:
            current_playing_status = self.player.is_playing()
            if self.is_playing != current_playing_status:
                self.is_playing = current_playing_status
                self.bus.send_manager_event(Tuner.EVENT_PLAY_STATUS, self.status())


class TunerStatusLED(RadioItem):
    CODE = "led"
    EVENT_TUNER_STATUS = "status"

    def __init__(self, pin):
        super(TunerStatusLED, self).__init__(Bus(LED_OUTPUT_LOG, TunerStatusLED.CODE))
        self.led = LED(pin)
        self.led.off()

    def exit(self):
        self.led.off()

    def loop(self):
        if (event := self.bus.consume_event(TunerStatusLED.EVENT_TUNER_STATUS)) is not None:

            if event.status == TunerStatus.PLAYING:
                self.led.on()

            elif event.status == TunerStatus.TUNING:
                self.led.start_blink()

            else:
                self.led.off()


class Display(RadioItem):
    CODE = "display"
    EVENT_VOLUME = "volume"
    EVENT_TUNER_STATUS = "status"

    def __init__(self, loop_sleep = None):
        super(Display, self).__init__(Bus(DISPLAY_OUTPUT_LOG, Display.CODE), loop_sleep=loop_sleep)
        self.oled = OLED_1in32.OLED_1in32()
        self.oled.Init()
        self.oled.clear()
        self.manager = DisplayManager()
        self.manager.welcome()

    def exit(self):
        self.oled.clear()
        self.oled.module_exit()

    def loop(self):
        if (event := self.bus.consume_event(Display.EVENT_VOLUME)) is not None:
            self.manager.volume(event)
        if (event := self.bus.consume_event(Display.EVENT_TUNER_STATUS)) is not None:
            self.manager.tuner_status(event)

        self.oled.ShowImage(self.oled.getbuffer(self.manager.display()))
