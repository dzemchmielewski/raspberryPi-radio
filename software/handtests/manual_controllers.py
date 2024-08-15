#!/usr/bin/python
from bus import Bus
from controlers import RecognizeController, AbstractVolumeController, AbstractStationController, DummyController
from entities import RadioItem


class KeyboardController(RadioItem):
    CODE = "keyboard"

    def __init__(self, station_ctr, volume_ctr):
        super(KeyboardController, self).__init__(Bus("KBRD-CTR", KeyboardController.CODE))
        self.volume_ctrl = volume_ctr
        self.station_ctrl = station_ctr

    def loop(self):
        some_input = input(" STATION (type: up, down, r)  VOLUME (type: vup, vdown, vmute) SCREEN (type: ss) >> \n")
        match some_input:
            case "up":
                self.station_ctrl.rotated('R')
            case "down":
                self.station_ctrl.rotated('L')
            case "vup":
                self.volume_ctrl.rotated('R')
            case "vdown":
                self.volume_ctrl.rotated('L')
            case "vmute":
                self.volume_ctrl.clicked()
            case "r":
                self.bus.send_manager_event(RecognizeController.EVENT_RECOGNIZE, True)
            case "ss":
                self.bus.send_manager_event(DummyController.EVENT_DUMMY, True)
                pass
            case "":
                # do nothing
                pass
            case _:
                print("Unrecognized action!")

    def exit(self):
        pass


class ManualStationController(AbstractStationController):
    def __init__(self):
        super(ManualStationController, self).__init__()


class ManualVolumeController(AbstractVolumeController):
    def __init__(self):
        super(ManualVolumeController, self).__init__()


if __name__ == "__main__":
    try:
        keyboard = KeyboardController(ManualStationController(), ManualVolumeController())
        keyboard.run()
    except KeyboardInterrupt:
        pass
    finally:
        keyboard.exit()
