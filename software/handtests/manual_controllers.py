#!/usr/bin/python
from alsaaudio import Mixer

from bus import Bus
from configuration import RT_CURRENT_STATION, STATIONS, DISPLAY_WIDTH, DISPLAY_HEIGHT
from entities import RadioItem, STATION_CONTROLLER_LOG, DISPLAY_OUTPUT_LOG, now
from controlers import StationController, VolumeController, RecognizeController, AbstractVolumeController
from display_manager import DisplayManager
from outputs import Display


class KeyboardController(RadioItem):
    CODE = StationController.CODE

    def __init__(self):
        super(KeyboardController, self).__init__(Bus(STATION_CONTROLLER_LOG, StationController.CODE))
        self.volume_ctrl = ManualVolumeController()
        self.stations_count = len(STATIONS)
        saved_station = self.bus.get(RT_CURRENT_STATION)
        if saved_station is None:
            self.current_station = 0
            self.bus.set(RT_CURRENT_STATION, self.current_station)
        else:
            self.current_station = saved_station
        self.bus.send_manager_event(StationController.EVENT_STATION_SET, self.current_station)

    def loop(self):
        some_input = input(" STATION (type: up, down)  VOLUME (type: vup, vdown, vmute >> \n")
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

            case "vup":
                self.volume_ctrl.rotated('R')
            case "vdown":
                self.volume_ctrl.rotated('L')
            case "vmute":
                self.volume_ctrl.clicked()

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


class ManualVolumeController(AbstractVolumeController):
    def __init__(self):
        super(ManualVolumeController, self).__init__(VolumeController.CODE)

class ManualDisplay(RadioItem):
    CODE = Display.CODE

    def __init__(self, loop_sleep=None):
        super(ManualDisplay, self).__init__(Bus(DISPLAY_OUTPUT_LOG, Display.CODE), loop_sleep=loop_sleep)
        self.manager = DisplayManager(DISPLAY_WIDTH, DISPLAY_HEIGHT)
        self.last_astro_req_sent = None

    def exit(self):
        pass

    def loop(self):
        if (event := self.bus.consume_event(Display.EVENT_VOLUME)) is not None:
            self.manager.volume(event)
        if (event := self.bus.consume_event(Display.EVENT_TUNER_STATUS)) is not None:
            self.manager.tuner_status(event)
        if (event := self.bus.consume_event(Display.EVENT_RECOGNIZE_STATUS)) is not None:
            self.manager.recognize_status(event)
        if (event := self.bus.consume_event(Display.EVENT_ASTRO_DATA)) is not None:
            self.manager.astro(event)

        if (astro_date := self.manager.new_astro()) is not None:
            # don't send request event more often, then once a minute
            if self.last_astro_req_sent is None or (now() > self.last_astro_req_sent + 60 * 1_000):
                self.last_astro_req_sent = now()
                self.bus.send_manager_event(Display.EVENT_REQUIRE_ASTRO_DATA, astro_date)

        image = self.manager.display()
        image = image.point(lambda p: p * 16)
        image.save("out.bmp")
