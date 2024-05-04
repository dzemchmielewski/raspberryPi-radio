#!/usr/bin/python

from bus import Bus
from configuration import FULL_LOAD, DISPLAY_WIDTH, DISPLAY_HEIGHT
from entities import TunerStatus, RadioItem,LED_OUTPUT_LOG, DISPLAY_OUTPUT_LOG, RecognizeState
from display_manager import DisplayManager

if FULL_LOAD:
    from hardware import LED
    from oled.lib import OLED_1in32


class LEDIndicator(RadioItem):
    CODE = "led"
    EVENT_TUNER_STATUS = "play_status"
    EVENT_RECOGNIZE_STATUS = "rec_status"

    def __init__(self, pin_play, pin_rec):
        super(LEDIndicator, self).__init__(Bus(LED_OUTPUT_LOG, LEDIndicator.CODE))
        self.led_play = LED(pin_play)
        self.led_rec = LED(pin_rec)
        self.led_play.off()
        self.led_rec.off()

    def exit(self):
        self.led_play.off()
        self.led_rec.off()

    def loop(self):
        if (event := self.bus.consume_event(LEDIndicator.EVENT_TUNER_STATUS)) is not None:

            if event.status == TunerStatus.PLAYING:
                self.led_play.on()

            elif event.status == TunerStatus.TUNING:
                self.led_play.start_blink()

            else:
                self.led_play.off()

        if (event := self.bus.consume_event(LEDIndicator.EVENT_RECOGNIZE_STATUS)) is not None:

            if event.state == RecognizeState.CONNECTING or event.state == RecognizeState.RECORDING:
                self.led_rec.start_blink()
            elif event.state == RecognizeState.QUERYING:
                self.led_rec.on()
            else:
                self.led_rec.off()


class Display(RadioItem):
    CODE = "display"
    EVENT_VOLUME = "volume"
    EVENT_TUNER_STATUS = "status"
    EVENT_TUNER_PLAY_INFO = "playinfo"
    EVENT_SELECT_STATION = "select_station"
    EVENT_RECOGNIZE_STATUS = "recognize"
    EVENT_ASTRO_DATA = "astro"
    EVENT_METEO_DATA = "meteo"
    EVENT_HOLIDAY_DATA = "holiday"
    EVENT_SCREENSAVER = "screensaver"

    def __init__(self, loop_sleep=None):
        super(Display, self).__init__(Bus(DISPLAY_OUTPUT_LOG, Display.CODE), loop_sleep=loop_sleep)
        self.manager = DisplayManager(DISPLAY_WIDTH, DISPLAY_HEIGHT)

    def loop(self):
        if (event := self.bus.consume_event(Display.EVENT_VOLUME)) is not None:
            self.manager.volume(event)
        if (event := self.bus.consume_event(Display.EVENT_TUNER_STATUS)) is not None:
            self.manager.tuner_status(event)
        if (event := self.bus.consume_event(Display.EVENT_SELECT_STATION)) is not None:
            self.manager.select_station(event)
        if (event := self.bus.consume_event(Display.EVENT_TUNER_PLAY_INFO)) is not None:
            self.manager.tuner_play_info(event)
        if (event := self.bus.consume_event(Display.EVENT_RECOGNIZE_STATUS)) is not None:
            self.manager.recognize_status(event)
        if (event := self.bus.consume_event(Display.EVENT_ASTRO_DATA)) is not None:
            self.manager.astro(event)
        if (event := self.bus.consume_event(Display.EVENT_METEO_DATA)) is not None:
            self.manager.meteo(event)
        if (event := self.bus.consume_event(Display.EVENT_HOLIDAY_DATA)) is not None:
            self.manager.holiday(event)
        if (event := self.bus.consume_event(Display.EVENT_SCREENSAVER)) is not None:
            self.manager.screensaver(event)


class OLEDDisplay(Display):
    def __init__(self, loop_sleep=None):
        super(OLEDDisplay, self).__init__(loop_sleep=loop_sleep)
        self.oled = OLED_1in32.OLED_1in32()
        self.oled.Init()
        self.oled.clear()

    def exit(self):
        self.oled.clear()
        self.oled.module_exit()

    def loop(self):
        super(OLEDDisplay, self).loop()
        self.oled.ShowImage(self.oled.getbuffer(self.manager.display()))


class FileOutputDisplay(Display):

    def __init__(self, loop_sleep=None):
        super(FileOutputDisplay, self).__init__(loop_sleep=loop_sleep)

    def exit(self):
        pass

    def loop(self):
        super(FileOutputDisplay, self).loop()
        image = self.manager.display()
        image = image.point(lambda p: p * 16)
        image.save("out.bmp")
