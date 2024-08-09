#!/usr/bin/python
from datetime import datetime, date
from enum import Enum
from abc import ABC, abstractmethod
from time import sleep, time

RADIO_MANAGER_CODE = "radio"
EVENT_EXIT = "exit"

RADIO_LOG = "RADIO   "
STATION_CONTROLLER_LOG = "STAT-CTR"
VOLUME_CONTROLLER_LOG = "VOL-CTR "
RECOGNIZE_CONTROLLER_LOG = "REC-CTR "
ASTRO_CONTROLLER_LOG = "ASTR-CTR"
METEO_CONTROLLER_LOG = "METE-CTR"
DUMMY_CONTROLLER_LOG = "DUMM-CTR"
WHOISHOME_CONTROLLER_LOG = "HOME-CTR"
HOLIDAY_CONTROLLER_LOG = "HOLI-CTR"
LED_OUTPUT_LOG = "LED     "
TUNER_OUTPUT_LOG = "TUNER   "
DISPLAY_OUTPUT_LOG = "DISPLAY "
TRACK_OUTPUT_LOG = "TRACK   "

SECOND = 1_000
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE


def now() -> int:
    return round(time() * 1_000)


def time_f(t: datetime) -> str:
    if t is not None:
        return t.strftime("%H:%M")
    return "--:--"


class Station:

    def __init__(self, name, code, url):
        self.name = name
        self.code = code
        self.url = url

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "[" + self.code + "][" + self.name + "][" + self.url + "]"

    def __hash__(self):
        return hash((self.code, self.name, self.url))

    def __eq__(self, other):
        if not isinstance(other, Station):
            return NotImplemented
        return self.name == other.name and self.code == other.code and self.url == other.url


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


class AstroData:
    def __init__(self, day: date, sunrise: datetime, sunset: datetime, moonrise: datetime, moonset: datetime, moon_phase: float):
        self.day = day
        self.sunrise = sunrise
        self.sunset = sunset
        self.moonrise = moonrise
        self.moonset = moonset
        self.moon_phase = moon_phase

    def __str__(self):
        return ("ASTRO[" + self.day.strftime("%Y-%m-%d") + "]"
                + "[" + time_f(self.sunrise) + " " + time_f(self.sunset) + "]"
                + "[" + time_f(self.moonrise) + " " + time_f(self.moonset) + "]"
                + "[" + str(self.moon_phase) + "]")

    def __hash__(self):
        return hash((self.day, self.sunrise, self.sunset, self.moonrise, self.moonset, self.moon_phase))


class MeteoData:
    compass_sectors = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW", "N"]

    def __init__(self, datetime, description, icon, temperature, pressure, conditions, windgust, windspeed, winddir):
        self.datetime = datetime
        self.description = description
        self.icon = icon
        self.temperature = temperature
        self.pressure = pressure
        self.conditions = conditions
        self.windgust = windgust
        self.windspeed = windspeed
        self.winddir = winddir

    def winddir_compass(self):
        return self.compass_sectors[round(self.winddir / 22.5)]

    def __str__(self):
        return ("METEO[" + self.datetime.strftime("%Y-%m-%d %H:%M:%S") + "]"
                + "[{}C,{}hPa][{}, wind: ({} - {}, {}) - {}]".format(self.temperature, self.pressure, self.icon, self.winddir,
                                                                     self.winddir_compass(), self.windspeed, self.description))

    def __hash__(self):
        return hash((self.datetime, self.description, self.icon, self.temperature, self.pressure, self.conditions, self.windspeed,
                     self.windspeed, self.winddir))


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
        return "[" + str(self.state) + "][" + self.station.code + "]"


class RadioItem(ABC):

    def __init__(self, bus, loop_sleep=0.2, on_run_callback=None):
        self.bus = bus
        self.loop_sleep = loop_sleep
        self.on_run_callback = on_run_callback
        self.bus.log("START (loop: " + str(self.loop_sleep) + ")")

    @abstractmethod
    def loop(self):
        pass

    @abstractmethod
    def exit(self):
        pass

    def run(self):
        if self.on_run_callback is not None:
            self.on_run_callback()
        while self.bus.consume_event(EVENT_EXIT) is None:
            self.loop()
            sleep(self.loop_sleep)
        self.bus.exit()
        self.exit()
        self.bus.log("EXIT")
