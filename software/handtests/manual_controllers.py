#!/usr/bin/python
from alsaaudio import Mixer

from bus import Bus
from configuration import RT_CURRENT_STATION, STATIONS, DISPLAY_WIDTH, DISPLAY_HEIGHT
from entities import RadioItem, VolumeStatus, VolumeEvent, STATION_CONTROLLER_LOG, VOLUME_CONTROLLER_LOG, DISPLAY_OUTPUT_LOG
from controlers import StationController, VolumeController, RecognizeController
from display_manager import DisplayManager
from outputs import Display


class ManualStationController(RadioItem):
    CODE = StationController.CODE

    def __init__(self):
        super(ManualStationController, self).__init__(Bus(STATION_CONTROLLER_LOG, StationController.CODE))
        self.stations_count = len(STATIONS)
        saved_station = self.bus.get(RT_CURRENT_STATION)
        if saved_station is None:
            self.current_station = 0
            self.bus.set(RT_CURRENT_STATION, self.current_station)
        else:
            self.current_station = saved_station
        self.bus.send_manager_event(StationController.EVENT_STATION_SET, self.current_station)

    def loop(self):
        some_input = input(" STATION (type: up, down, set #) >> ")
        match some_input:
            case "up":
              if self.current_station + 1 < self.stations_count:
                  self.current_station = self.current_station + 1
              else:
                   self.current_station = 0
              self.bus.send_manager_event(StationController.EVENT_STATION_UP, self.current_station)

            case "down":
                if self.current_station - 1 >= 0:
                    self.current_station = self.current_station - 1
                else:
                    self.current_station = self.stations_count - 1
                self.bus.send_manager_event(StationController.EVENT_STATION_DOWN, self.current_station)

            case "set":
                number = input(" type in station number >> ")
                try:
                    self.bus.send_manager_event(StationController.EVENT_STATION_SET, int(number))
                except ValueError:
                    self.bus.log("Error converting to int: " + number)
            case "r":
                self.bus.send_manager_event(RecognizeController.EVENT_RECOGNIZE, True)

            case "":
                # do nothing
                pass
            case _:
                print("Unrecognized action!")
        self.bus.set(RT_CURRENT_STATION, self.current_station)


    def exit(self):
        pass


class ManualVolumeController(RadioItem):
    CODE = VolumeController.CODE

    def __init__(self):
        super(ManualVolumeController, self).__init__(Bus(VOLUME_CONTROLLER_LOG, ManualVolumeController.CODE))
        self.mixer = Mixer()

    def volume_change(self, delta):
        status = VolumeStatus(self.mixer.getvolume()[0], self.mixer.getmute()[0])

        if 0 <= status.volume + delta <= 100:
            new_status = VolumeStatus(status.volume + delta, status.is_muted)
        elif status.volume + delta < 0:
            new_status = VolumeStatus(0, status.is_muted)
        else:  # status.volume + delta > 100
            new_status = VolumeStatus(100, status.is_muted)

        if delta >= 0:
            self.bus.send_manager_event(VolumeController.EVENT_VOLUME_UP, VolumeEvent(status, new_status))
        else:  # delta < 0
            self.bus.send_manager_event(VolumeController.EVENT_VOLUME_DOWN, VolumeEvent(status, new_status))

        self.mixer.setvolume(status.volume + delta)

    def loop(self):
        some_input = input(" VOLUME (type: up, down, set #) >> ")
        match some_input:
            case "up":
                self.volume_change(VolumeController.DELTA)
            case "down":
                self.volume_change(-VolumeController.DELTA)
            case "":
                # do nothing
                pass
            case _:
                print("Unrecognized action!")

    def exit(self):
        pass


class ManualDisplay(RadioItem):

    CODE = Display.CODE

    def __init__(self, loop_sleep=None):
        super(ManualDisplay, self).__init__(Bus(DISPLAY_OUTPUT_LOG, Display.CODE), loop_sleep=loop_sleep)
        self.manager = DisplayManager(DISPLAY_WIDTH, DISPLAY_HEIGHT)

    def exit(self):
        pass

    def loop(self):
        if (event := self.bus.consume_event(Display.EVENT_VOLUME)) is not None:
            self.manager.volume(event)
        if (event := self.bus.consume_event(Display.EVENT_TUNER_STATUS)) is not None:
            self.manager.tuner_status(event)
        if (event := self.bus.consume_event(Display.EVENT_RECOGNIZE_STATUS)) is not None:
            self.manager.recognize_status(event)

        image = self.manager.display()
        image = image.point(lambda p: p * 16)
        image.save("out.bmp")
