#!/usr/bin/python
import json
import urllib
from datetime import datetime, timedelta
from threading import Thread
from urllib.request import urlopen

import requests
import vlc

from bus import Bus
from configuration import FULL_LOAD, AUDD_CLIP_DIRECTORY, AUDD_CLIP_DURATION, AUDD_URL, DISPLAY_WIDTH, DISPLAY_HEIGHT
from entities import TunerStatus, RadioItem, TUNER_OUTPUT_LOG, LED_OUTPUT_LOG, DISPLAY_OUTPUT_LOG, Station, \
    RecognizeStatus, RecognizeState, now
from display_manager import DisplayManager

if FULL_LOAD:
    from hardware import LED
    from oled.lib import OLED_1in32


class Tuner(RadioItem):
    CODE = "tuner"
    EVENT_STATION = "station"
    EVENT_PLAY_STATUS = "status"
    EVENT_RECOGNIZE = "recognize"
    EVENT_RECOGNIZE_STATUS = "recognize_status"

    def __init__(self):
        super(Tuner, self).__init__(Bus(TUNER_OUTPUT_LOG, Tuner.CODE))
        self.player = vlc.MediaPlayer()
        self.is_playing = False
        self.current_station = None
        self.recognizing_thread = None

    def exit(self):
        self.player.stop()

    def status(self):
        if self.is_playing:
            return TunerStatus.PLAYING
        return TunerStatus.TUNING

    def __recognize__(self, station: Station):
        self.bus.send_manager_event(Tuner.EVENT_RECOGNIZE_STATUS, RecognizeStatus(RecognizeState.CONNECTING, station))
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7"}
            request = urllib.request.Request(station.url, None, headers)
            stream = urllib.request.urlopen(request)
            # stream = urlopen(station.url)

            begin = datetime.now()
            duration = timedelta(milliseconds=AUDD_CLIP_DURATION)
            file_path = AUDD_CLIP_DIRECTORY + station.code + "-" + str(begin) + ".mp3"
            fd = open(file_path, "wb")

            self.bus.send_manager_event(Tuner.EVENT_RECOGNIZE_STATUS, RecognizeStatus(RecognizeState.RECORDING, station))
            while datetime.now() - begin < duration:
                data = stream.read(10000)
                fd.write(data)
            fd.close()

            self.bus.send_manager_event(Tuner.EVENT_RECOGNIZE_STATUS, RecognizeStatus(RecognizeState.QUERYING, station))

            with open(file_path, "rb") as f:
                r = requests.post(AUDD_URL, files={'file': f})
                response = json.loads(r.text)

            self.bus.send_manager_event(Tuner.EVENT_RECOGNIZE_STATUS, RecognizeStatus(RecognizeState.DONE, station, response))

        except requests.exceptions.RequestException as e:
            self.bus.log("Error querying AudD: " + str(e))
            self.bus.send_manager_event(Tuner.EVENT_RECOGNIZE_STATUS,
                                        RecognizeStatus(RecognizeState.DONE, station, json.loads("{\"status\":\"error\"}")))

        except urllib.error.HTTPError as e:
            self.bus.log("Error opening stream (" + station.url + "): " + str(e))
            self.bus.send_manager_event(Tuner.EVENT_RECOGNIZE_STATUS,
                                        RecognizeStatus(RecognizeState.DONE, station, json.loads("{\"status\":\"error\"}")))

    def loop(self):
        if (station := self.bus.consume_event(Tuner.EVENT_STATION)) is not None:
            if self.current_station != station or not self.is_playing:
                # First notify about the sound break:
                self.is_playing = False
                self.bus.send_manager_event(Tuner.EVENT_PLAY_STATUS, self.status())
                # Then change the station:
                # self.bus.log("Playing " + str(station))
                self.current_station = station
                self.player.set_media(vlc.Media(station.url))
                self.player.play()
            else:
                # already playing that station...
                self.bus.send_manager_event(Tuner.EVENT_PLAY_STATUS, self.status())

        elif self.bus.consume_event(Tuner.EVENT_RECOGNIZE) is not None:
            if self.recognizing_thread is None or not self.recognizing_thread.is_alive():
                self.recognizing_thread = Thread(target=self.__recognize__, args=[self.current_station])
                self.recognizing_thread.start()

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
    EVENT_RECOGNIZE_STATUS = "recognize"
    EVENT_ASTRO_DATA = "astro"
    EVENT_METEO_DATA = "meteo"
    EVENT_SCREENSAVER = "screensaver"

    def __init__(self, loop_sleep=None):
        super(Display, self).__init__(Bus(DISPLAY_OUTPUT_LOG, Display.CODE), loop_sleep=loop_sleep)
        self.manager = DisplayManager(DISPLAY_WIDTH, DISPLAY_HEIGHT)

    def loop(self):
        if (event := self.bus.consume_event(Display.EVENT_VOLUME)) is not None:
            self.manager.volume(event)
        if (event := self.bus.consume_event(Display.EVENT_TUNER_STATUS)) is not None:
            self.manager.tuner_status(event)
        if (event := self.bus.consume_event(Display.EVENT_RECOGNIZE_STATUS)) is not None:
            self.manager.recognize_status(event)
        if (event := self.bus.consume_event(Display.EVENT_ASTRO_DATA)) is not None:
            self.manager.astro(event)
        if (event := self.bus.consume_event(Display.EVENT_METEO_DATA)) is not None:
            self.manager.meteo(event)
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
