#!/usr/bin/python
import vlc

from bus import Bus
from configuration import FULL_LOAD
from entities import TunerStatus, RadioItem, TUNER_OUTPUT_LOG, LED_OUTPUT_LOG, DISPLAY_OUTPUT_LOG

if FULL_LOAD:
    from hardware import LED
    from oled.lib import OLED_1in32

from oled.picture_creator import PictureCreator


class Tuner(RadioItem):
    CODE = "tuner"
    EVENT_STATION = "station"
    EVENT_PLAY_STATUS = "status"

    def __init__(self):
        super(Tuner, self).__init__(Bus(TUNER_OUTPUT_LOG, Tuner.CODE))
        self.player = vlc.MediaPlayer()
        self.is_playing = False

    def exit(self):
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


class TunerStatusLED(RadioItem):
    CODE = "led"
    EVENT_STATUS = "status"

    def __init__(self, pin):
        super(TunerStatusLED, self).__init__(Bus(LED_OUTPUT_LOG, TunerStatusLED.CODE))
        self.led = LED(pin)
        self.led.off()

    def exit(self):
        self.led.off()

    def loop(self):
        if (event := self.bus.consume_event(TunerStatusLED.EVENT_STATUS)) is not None:

            if event.status == TunerStatus.PLAYING:
                self.led.on()

            elif event.status == TunerStatus.TUNING:
                self.led.start_blink()

            else:
                self.led.off()


class Display(RadioItem):
    CODE = "display"
    EVENT_VOLUME = "volume"

    def __init__(self):
        super(Display, self).__init__(Bus(DISPLAY_OUTPUT_LOG, Display.CODE))
        self.oled = OLED_1in32.OLED_1in32()
        self.oled.Init()
        self.oled.clear()
        self.creator = PictureCreator()

    def exit(self):
        self.oled.clear()
        self.oled.module_exit()

    def loop(self):
        if (event := self.bus.consume_event(Display.EVENT_VOLUME)) is not None:
            self.creator.volume_method_to_refactor(event)

        self.oled.ShowImage(self.oled.getbuffer(self.creator.main()))
