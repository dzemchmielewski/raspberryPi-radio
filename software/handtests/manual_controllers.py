#!/usr/bin/python
from alsaaudio import Mixer

from bus import Bus
from entities import RadioItem, VolumeStatus, VolumeEvent
from controlers import StationController, VolumeController


# DEPRECATED - will be removed
class ManualStationController(RadioItem):
    CODE = StationController.CODE

    def __init__(self):
        super(ManualStationController, self).__init__(Bus("STATION-CTRL", StationController.CODE))

    def loop(self):
        some_input = input(" STATION (type: up, down, set #) >> ")
        match some_input:
            case "up":
                self.bus.send_manager_event(StationController.EVENT_STATION_UP, True)
            case "down":
                self.bus.send_manager_event(StationController.EVENT_STATION_DOWN, True)
            case "set":
                number = input(" type in station number >> ")
                try:
                    self.bus.send_manager_event(StationController.EVENT_STATION_SET, int(number))
                except ValueError:
                    self.bus.log("Error converting to int: " + number)
            case "":
                # do nothing
                pass
            case _:
                print("Unrecognized action!")


class ManualVolumeController(RadioItem):
    CODE = VolumeController.CODE

    def __init__(self):
        super(ManualVolumeController, self).__init__(Bus("VOLUME-CTRL", ManualVolumeController.CODE))
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
