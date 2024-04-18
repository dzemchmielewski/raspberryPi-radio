#!/usr/bin/python
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
from time import sleep, time

RADIO_MANAGER_CODE = "radio"
EVENT_EXIT = "exit"

RADIO_LOG = "RADIO   "
STATION_CONTROLLER_LOG = "STAT-CTR"
VOLUME_CONTROLLER_LOG = "VOL-CTR "
RECOGNIZE_CONTROLLER_LOG = "RECG-CTR"
ACCUWEATHER_CONTROLLER_LOG = "ACCUWTHR"
LED_OUTPUT_LOG = "LED     "
TUNER_OUTPUT_LOG = "TUNER   "
DISPLAY_OUTPUT_LOG = "DISPLAY "


def now() -> int:
    return round(time() * 1_000)


class Station:

    def __init__(self, name, code, url):
        self.name = name
        self.code = code
        self.url = url

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "[" + self.code + "][" + self.name + "][" + self.url + "]"


class TunerStatus(Enum):
    PLAYING = "P"
    TUNING = "N"
    UNKNOWN = "U"

    def __str__(self):
        return self.name


class VolumeStatus:
    def __init__(self, volume, is_muted):
        self.volume = volume
        self.is_muted = is_muted

    def __str__(self):
        return "[volume " + str(self.volume) + "(" + str(self.is_muted) + ")]"


class Status:
    def __init__(self, status: TunerStatus, station: Station):
        self.status = status
        self.station = station

    def __str__(self):
        return "[" + str(self.status) + "][" + self.station.code + "]"


class VolumeEvent:
    def __init__(self, previous_status: VolumeStatus, current_status: VolumeStatus):
        self.previous_status = previous_status
        self.current_status = current_status

    def __str__(self):
        return "[" + str(self.previous_status) + " => " + str(self.current_status) + "]"


class AstroDay:
    def __init__(self, sunrise:datetime=None, sunset:datetime=None, moonrise:datetime=None, moonset:datetime=None, moon_phase:float=0):
        self.sunrise = sunrise
        self.sunset = sunset
        self.moonrise = moonrise
        self.moonset = moonset
        self.moon_phase = moon_phase




class AstroEvent:
    def __init__(self, today: AstroDay = AstroDay(), tomorrow: AstroDay = AstroDay()):
        self.today = today
        self.tomorrow = tomorrow


class WeatherEvent:
    def __init__(self, current, forecast):
        self.current = current
        self.forecast = forecast

    def dates(self):
        return self.current[0]["LocalObservationDateTime"], self.forecast["Headline"]["EffectiveDate"]

    def __str__(self):
        return "[" + str(self.dates()) + "]"


class RecognizeState(Enum):
    CONNECTING = "C"
    RECORDING = "R"
    QUERYING = "Q"
    DONE = "D"

    def __str__(self):
        return self.name


class RecognizeStatus:
    def __init__(self, state: RecognizeState, station: Station, json=None):
        self.state = state
        self.station = station
        self.json = json

    def __str__(self):
        return "[" + str(self.state) + "][" + self.station.code + "][" + str(self.json) + "]"


class RadioItem(ABC):

    def __init__(self, bus, loop_sleep=0.3):
        self.bus = bus
        self.loop_sleep = loop_sleep
        self.bus.log("START (loop: " + str(self.loop_sleep) + ")")

    @abstractmethod
    def loop(self):
        pass

    @abstractmethod
    def exit(self):
        pass

    def run(self, ):
        while self.bus.consume_event(EVENT_EXIT) is None:
            self.loop()
            sleep(self.loop_sleep)
        self.exit()
        self.bus.log("EXIT")
