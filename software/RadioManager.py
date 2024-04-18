#!/usr/bin/python
from threading import Thread

from bus import Bus
from configuration import STATIONS, RE2_LEFT_PIN, RE2_RIGHT_PIN, RE2_CLICK_PIN, RE1_CLICK_PIN, RE1_RIGHT_PIN, RE1_LEFT_PIN, \
    LED_RED_PIN, FULL_LOAD, BTN2_PIN
from entities import RADIO_MANAGER_CODE, Status, EVENT_EXIT, RadioItem, TunerStatus, RADIO_LOG
from controlers import StationController, VolumeController, RecognizeController, AccuweatherController
from handtests.manual_controllers import ManualStationController, ManualVolumeController, ManualDisplay
from outputs import Tuner, TunerStatusLED, Display


class RadioManager(RadioItem):

    def __init__(self, loop_sleep=None):
        super(RadioManager, self).__init__(Bus(RADIO_LOG, RADIO_MANAGER_CODE), loop_sleep=loop_sleep)
        self.current_station = None

    def exit(self):
        pass

    def loop(self):
        if (event := self.bus.consume_event(StationController.EVENT_STATION_UP)) is not None:
            self.current_station = event
            self.bus.send_event(TunerStatusLED.CODE, TunerStatusLED.EVENT_TUNER_STATUS, Status(TunerStatus.UNKNOWN, STATIONS[event]))
            self.bus.send_event(Display.CODE, Display.EVENT_TUNER_STATUS, Status(TunerStatus.UNKNOWN, STATIONS[event]))
            self.bus.send_event(Tuner.CODE, Tuner.EVENT_STATION, STATIONS[event])

        if (event := self.bus.consume_event(StationController.EVENT_STATION_DOWN)) is not None:
            self.current_station = event
            self.bus.send_event(TunerStatusLED.CODE, TunerStatusLED.EVENT_TUNER_STATUS, Status(TunerStatus.UNKNOWN, STATIONS[event]))
            self.bus.send_event(Display.CODE, Display.EVENT_TUNER_STATUS, Status(TunerStatus.UNKNOWN, STATIONS[event]))
            self.bus.send_event(Tuner.CODE, Tuner.EVENT_STATION, STATIONS[event])

        if (event := self.bus.consume_event(StationController.EVENT_STATION_SET)) is not None:
            self.current_station = event
            self.bus.send_event(TunerStatusLED.CODE, TunerStatusLED.EVENT_TUNER_STATUS, Status(TunerStatus.UNKNOWN, STATIONS[event]))
            self.bus.send_event(Display.CODE, Display.EVENT_TUNER_STATUS, Status(TunerStatus.UNKNOWN, STATIONS[event]))
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
            self.bus.send_event(TunerStatusLED.CODE, TunerStatusLED.EVENT_TUNER_STATUS, Status(event, STATIONS[self.current_station]))
            self.bus.send_event(Display.CODE, Display.EVENT_TUNER_STATUS, Status(event, STATIONS[self.current_station]))

        if self.bus.consume_event(RecognizeController.EVENT_RECOGNIZE) is not None:
            self.bus.send_event(Tuner.CODE, Tuner.EVENT_RECOGNIZE, True)

        if (event := self.bus.consume_event(Tuner.EVENT_RECOGNIZE_STATUS)) is not None:
            self.bus.send_event(Display.CODE, Display.EVENT_RECOGNIZE_STATUS, event)

if __name__ == "__main__":

    radio = RadioManager(0.1)

    if FULL_LOAD:
        jobs = (
            Tuner(),
            TunerStatusLED(LED_RED_PIN),
            VolumeController(RE1_LEFT_PIN, RE1_RIGHT_PIN, RE1_CLICK_PIN),
            StationController(RE2_LEFT_PIN, RE2_RIGHT_PIN, RE2_CLICK_PIN),
            RecognizeController(BTN2_PIN),
            Display(0.1),
            # AccuweatherController()
        )
    else:
        jobs = (
            Tuner(),
            ManualStationController(),
            ManualDisplay(0.1),
            # AccuweatherController()
            # ManualVolumeController()
        )

    threads = [Thread(target=x.run) for x in jobs]

    try:
        [t.start() for t in threads]
        radio.run()
    except KeyboardInterrupt:
        pass
    finally:
        for i in range(len(jobs)):
            if threads[i].is_alive():
                radio.bus.send_event(jobs[i].CODE, EVENT_EXIT, True)
                threads[i].join()
        print("RADIO BYE")
