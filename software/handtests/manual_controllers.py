#!/usr/bin/python
from bus import Bus
from configuration import DISPLAY_WIDTH, DISPLAY_HEIGHT
from entities import RadioItem, DISPLAY_OUTPUT_LOG, now
from controlers import VolumeController, RecognizeController, AbstractVolumeController, AbstractStationController
from display_manager import DisplayManager
from outputs import Display


class KeyboardController(RadioItem):
    CODE = "keyboard"

    def __init__(self):
        super(KeyboardController, self).__init__(Bus("KBRD-CTR", KeyboardController.CODE))
        self.volume_ctrl = ManualVolumeController()
        self.station_ctrl = ManualStationController()

    def loop(self):
        some_input = input(" STATION (type: up, down)  VOLUME (type: vup, vdown, vmute >> \n")
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
            case "":
                # do nothing
                pass
            case _:
                print("Unrecognized action!")

    def exit(self):
        self.volume_ctrl.bus.exit()
        self.station_ctrl.bus.exit()


class ManualStationController(AbstractStationController):
    def __init__(self):
        super(ManualStationController, self).__init__()


class ManualVolumeController(AbstractVolumeController):
    def __init__(self):
        super(ManualVolumeController, self).__init__()


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

        if (event := self.bus.consume_event(Display.EVENT_SCREENSAVER)) is not None:
            self.manager.screensaver(event)

        image = self.manager.display()
        image = image.point(lambda p: p * 16)
        image.save("out.bmp")
