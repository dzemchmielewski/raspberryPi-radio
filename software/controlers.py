#!/usr/bin/python
from alsaaudio import Mixer

from bus import Bus
from configuration import STATIONS, RT_CURRENT_STATION, STATION_PIN_LEFT, STATION_PIN_RIGHT, VOLUME_PIN_LEFT, VOLUME_PIN_RIGHT, \
    VOLUME_PIN_CLICK
from entities import RadioItem, VolumeStatus, VolumeEvent, STATION_CONTROLLER_LOG, VOLUME_CONTROLLER_LOG
from inputs import RotaryEncoder, RotaryButton


class StationController(RadioItem):
    CODE = "station_ctrl"
    EVENT_STATION_UP = "station_up"
    EVENT_STATION_DOWN = "station_down"
    EVENT_STATION_SET = "station_set"

    def __init__(self):
        super(StationController, self).__init__(Bus(STATION_CONTROLLER_LOG, StationController.CODE))
        self.encoder = RotaryEncoder(STATION_PIN_LEFT, STATION_PIN_RIGHT, self.rotated)
        self.stations_count = len(STATIONS)
        saved_station = self.bus.get(RT_CURRENT_STATION)
        if saved_station is None:
            self.current_station = 0
            self.bus.set(RT_CURRENT_STATION, self.current_station)
        else:
            self.current_station = saved_station
        self.bus.send_manager_event(StationController.EVENT_STATION_SET, self.current_station)

    def rotated(self, direction):
        if direction == RotaryEncoder.DIRECTION_RIGHT:
            if self.current_station + 1 < self.stations_count:
                self.current_station = self.current_station + 1
            else:
                self.current_station = 0
            self.bus.send_manager_event(StationController.EVENT_STATION_UP, self.current_station)
        else:  # direction == RotaryEncoder.DIRECTION_LEFT
            if self.current_station - 1 >= 0:
                self.current_station = self.current_station - 1
            else:
                self.current_station = self.stations_count - 1
            self.bus.send_manager_event(StationController.EVENT_STATION_DOWN, self.current_station)
        self.bus.set(RT_CURRENT_STATION, self.current_station)

    def loop(self):
        pass


class VolumeController(RadioItem):
    CODE = "volume_ctrl"
    EVENT_VOLUME_UP = "volume_up"
    EVENT_VOLUME_DOWN = "volume_down"
    EVENT_VOLUME_MUTE = "volume_mute"
    EVENT_VOLUME_UNMUTE = "volume_unmute"
    DELTA = 3

    def __init__(self):
        super(VolumeController, self).__init__(Bus(VOLUME_CONTROLLER_LOG, VolumeController.CODE))
        self.encoder = RotaryEncoder(VOLUME_PIN_LEFT, VOLUME_PIN_RIGHT, self.rotated)
        self.button = RotaryButton(VOLUME_PIN_CLICK, self.clicked)
        self.mixer = Mixer()

    def calculate_volume(self, delta):
        volume = self.mixer.getvolume()[0]
        if 0 <= volume + delta <= 100:
            return volume + delta
        elif volume + delta < 0:
            return 0
        else:  # status.volume + delta > 100
            return 100

    def rotated(self, direction):
        status = VolumeStatus(self.mixer.getvolume()[0], self.mixer.getmute()[0])

        if direction == RotaryEncoder.DIRECTION_RIGHT:
            new_status = VolumeStatus(self.calculate_volume(VolumeController.DELTA), 0)
            if status.volume == 0:
                new_status.is_muted = 0
            self.bus.send_manager_event(VolumeController.EVENT_VOLUME_UP, VolumeEvent(status, new_status))
        else:
            new_status = VolumeStatus(self.calculate_volume(-VolumeController.DELTA), 0)
            if new_status.volume == 0:
                new_status.is_muted = 1
            self.bus.send_manager_event(VolumeController.EVENT_VOLUME_DOWN, VolumeEvent(status, new_status))

        self.mixer.setvolume(new_status.volume)
        if status.is_muted != new_status.is_muted:
            self.mixer.setmute(new_status.is_muted)

    def clicked(self):
        status = VolumeStatus(self.mixer.getvolume()[0], self.mixer.getmute()[0])
        new_status = VolumeStatus(status.volume, (status.is_muted + 1) % 2)
        if new_status.is_muted:
            self.bus.send_manager_event(VolumeController.EVENT_VOLUME_MUTE, VolumeEvent(status, new_status))
        else:
            # if unmute when volume is 0
            if new_status.volume == 0:
                # then set minimal volume:
                new_status.volume = VolumeController.DELTA
            self.bus.send_manager_event(VolumeController.EVENT_VOLUME_UNMUTE, VolumeEvent(status, new_status))
        self.mixer.setmute(new_status.is_muted)
        if status.volume != new_status.volume:
            self.mixer.setvolume(new_status.volume)

    def loop(self):
        pass
