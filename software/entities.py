#!/usr/bin/python

from enum import Enum
from abc import ABC, abstractmethod
from time import sleep

RADIO_MANAGER_CODE = "radio"
EVENT_EXIT = "exit"

RADIO_LOG = "RADIO   "
STATION_CONTROLLER_LOG = "STAT-CTR"
VOLUME_CONTROLLER_LOG = "VOL-CTR "
LED_OUTPUT_LOG = "LED     "
TUNER_OUTPUT_LOG = "TUNER   "
DISPLAY_OUTPUT_LOG = "DISPLAY "


class Station:
    SOME = "some"

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
    def __init__(self, status, station):
        self.status = status
        self.station = station

    def __str__(self):
        return "[" + str(self.status) + "][" + self.station.code + "]"


class VolumeEvent:
    def __init__(self, previous_status, current_status):
        self.previous_status = previous_status
        self.current_status = current_status

    def __str__(self):
        return "[" + str(self.previous_status) + " => " + str(self.current_status) + "]"


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

    def run(self,):
        while self.bus.consume_event(EVENT_EXIT) is None:
            self.loop()
            sleep(self.loop_sleep)
        self.exit()
        self.bus.log("EXIT")
