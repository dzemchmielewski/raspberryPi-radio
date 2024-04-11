#!/usr/bin/python
from threading import Thread

from bus import Bus
from configuration import STATIONS, RE2_LEFT_PIN, RE2_RIGHT_PIN, RE2_CLICK_PIN, RE1_CLICK_PIN, RE1_RIGHT_PIN, RE1_LEFT_PIN, \
    LED_RED_PIN, FULL_LOAD
from entities import RADIO_MANAGER_CODE, Status, EVENT_EXIT, RadioItem, TunerStatus, RADIO_LOG
from controlers import StationController, VolumeController
from handtests.manual_controllers import ManualStationController, ManualVolumeController, ManualDisplay
from outputs import Tuner, TunerStatusLED, Display


class RadioManager(RadioItem):

    def __init__(self):
        super(RadioManager, self).__init__(Bus(RADIO_LOG, RADIO_MANAGER_CODE))
        self.current_station = None

    def exit(self):
        pass

    def loop(self):
        if (event := self.bus.consume_event(StationController.EVENT_STATION_UP)) is not None:
            self.current_station = event
            self.bus.send_event(TunerStatusLED.CODE, TunerStatusLED.EVENT_STATUS, Status(TunerStatus.UNKNOWN, STATIONS[event]))
            self.bus.send_event(Tuner.CODE, Tuner.EVENT_STATION, STATIONS[event])

        if (event := self.bus.consume_event(StationController.EVENT_STATION_DOWN)) is not None:
            self.current_station = event
            self.bus.send_event(TunerStatusLED.CODE, TunerStatusLED.EVENT_STATUS, Status(TunerStatus.UNKNOWN, STATIONS[event]))
            self.bus.send_event(Tuner.CODE, Tuner.EVENT_STATION, STATIONS[event])

        if (event := self.bus.consume_event(StationController.EVENT_STATION_SET)) is not None:
            self.current_station = event
            self.bus.send_event(TunerStatusLED.CODE, TunerStatusLED.EVENT_STATUS, Status(TunerStatus.UNKNOWN, STATIONS[event]))
            self.bus.send_event(Tuner.CODE, Tuner.EVENT_STATION, STATIONS[event])

        if (event := self.bus.consume_event(VolumeController.EVENT_VOLUME_UP)) is not None:
            self.bus.send_event(Display.CODE, Display.EVENT_VOLUME, event)
        if (event := self.bus.consume_event(VolumeController.EVENT_VOLUME_DOWN)) is not None:
            self.bus.send_event(Display.CODE, Display.EVENT_VOLUME, event)
        if (event := self.bus.consume_event(VolumeController.EVENT_VOLUME_MUTE)) is not None:
            self.bus.send_event(Display.CODE, Display.EVENT_VOLUME, event)
        if (event := self.bus.consume_event(VolumeController.EVENT_VOLUME_UNMUTE)) is not None:
            self.bus.send_event(Display.CODE, Display.EVENT_VOLUME, event)

        if (event := self.bus.consume_event(Tuner.EVENT_PLAY_STATUS)) is not None:
            self.bus.send_event(TunerStatusLED.CODE, TunerStatusLED.EVENT_STATUS, Status(event, STATIONS[self.current_station]))


if __name__ == "__main__":

    radio = RadioManager()

    if FULL_LOAD:
        jobs = (
            Tuner(),
            TunerStatusLED(LED_RED_PIN),
            VolumeController(RE1_LEFT_PIN, RE1_RIGHT_PIN, RE1_CLICK_PIN),
            StationController(RE2_LEFT_PIN, RE2_RIGHT_PIN, RE2_CLICK_PIN),
            Display()
        )
    else:
        jobs = (
            Tuner(),
            ManualDisplay(),
            # ManualStationController(),
            ManualVolumeController()
        )

    threads = [Thread(target=x.main, args=[0.4]) for x in jobs]

    try:
        [t.start() for t in threads]
        radio.main(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for i in range(len(jobs)):
            if threads[i].is_alive():
                radio.bus.send_event(jobs[i].CODE, EVENT_EXIT, True)
                threads[i].join()
        print("RADIO BYE")
