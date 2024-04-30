#!/usr/bin/python
from threading import Thread

from bus import Bus
from configuration import STATIONS, RE2_LEFT_PIN, RE2_RIGHT_PIN, RE2_CLICK_PIN, RE1_CLICK_PIN, RE1_RIGHT_PIN, RE1_LEFT_PIN, \
    FULL_LOAD, BTN2_PIN, BTN3_PIN, BTN4_PIN, BTN5_PIN, LED_GREEN_PIN, LED_RED_PIN
from entities import RADIO_MANAGER_CODE, Status, EVENT_EXIT, RadioItem, TunerStatus, RADIO_LOG, now
from controlers import StationController, VolumeController, RecognizeController, AstroController, DummyController, MeteoController
from handtests.manual_controllers import KeyboardController
from outputs import Tuner, LEDIndicator, Display, OLEDDisplay, FileOutputDisplay
from whoishome import WhoIsHomeController


class RadioManager(RadioItem):

    def __init__(self, loop_sleep=None):
        super(RadioManager, self).__init__(Bus(RADIO_LOG, RADIO_MANAGER_CODE), loop_sleep=loop_sleep)
        self.current_station = None
        self.last_event = now()
        self.screensaver_activation_time = 5 * 60 * 1_000
        self.is_screensaver = False

    def exit(self):
        pass

    def loop(self):
        if (event := self.bus.consume_event(StationController.EVENT_STATION)) is not None:
            self.current_station = event
            self.bus.send_event(LEDIndicator.CODE, LEDIndicator.EVENT_TUNER_STATUS, Status(TunerStatus.UNKNOWN, STATIONS[event]))
            self.bus.send_event(Display.CODE, Display.EVENT_TUNER_STATUS, Status(TunerStatus.UNKNOWN, STATIONS[event]))
            self.bus.send_event(Tuner.CODE, Tuner.EVENT_STATION, STATIONS[event])
            self.last_event = now()

        if (event := self.bus.consume_event(VolumeController.EVENT_VOLUME)) is not None:
            self.bus.send_event(Display.CODE, Display.EVENT_VOLUME, event)
            self.last_event = now()

        if (event := self.bus.consume_event(Tuner.EVENT_PLAY_STATUS)) is not None:
            self.bus.send_event(LEDIndicator.CODE, LEDIndicator.EVENT_TUNER_STATUS, Status(event, STATIONS[self.current_station]))
            self.bus.send_event(Display.CODE, Display.EVENT_TUNER_STATUS, Status(event, STATIONS[self.current_station]))
            self.last_event = now()

        if self.bus.consume_event(RecognizeController.EVENT_RECOGNIZE) is not None:
            self.bus.send_event(Tuner.CODE, Tuner.EVENT_RECOGNIZE, True)
            self.last_event = now()
        if (event := self.bus.consume_event(Tuner.EVENT_RECOGNIZE_STATUS)) is not None:
            self.bus.send_event(Display.CODE, Display.EVENT_RECOGNIZE_STATUS, event)
            self.bus.send_event(LEDIndicator.CODE, LEDIndicator.EVENT_RECOGNIZE_STATUS, event)
            self.last_event = now()

        if (event := self.bus.consume_event(AstroController.EVENT_ASTRO_DATA)) is not None:
            self.bus.send_event(Display.CODE, Display.EVENT_ASTRO_DATA, event)
        if (event := self.bus.consume_event(MeteoController.EVENT_METEO_DATA)) is not None:
            self.bus.send_event(Display.CODE, Display.EVENT_METEO_DATA, event)

        if self.bus.consume_event(DummyController.EVENT_DUMMY) is not None:
            if self.is_screensaver:
                self.last_event = now()
            else:
                self.last_event = now() - self.screensaver_activation_time

        if self.is_screensaver:
            if self.last_event + self.screensaver_activation_time > now():
                self.bus.send_event(Display.CODE, Display.EVENT_SCREENSAVER, False)
                self.is_screensaver = False
        else:
            if self.last_event + self.screensaver_activation_time < now():
                self.bus.send_event(Display.CODE, Display.EVENT_SCREENSAVER, True)
                self.is_screensaver = True


if __name__ == "__main__":

    radio = RadioManager(0.1)

    if FULL_LOAD:
        jobs = (
            OLEDDisplay(0.1),
            Tuner(),
            LEDIndicator(LED_GREEN_PIN, LED_RED_PIN),
            StationController(RE2_LEFT_PIN, RE2_RIGHT_PIN),
            VolumeController(RE1_LEFT_PIN, RE1_RIGHT_PIN, RE1_CLICK_PIN),
            RecognizeController(RE2_CLICK_PIN),
            DummyController(BTN2_PIN, BTN3_PIN, BTN4_PIN, BTN5_PIN),
            AstroController(),
            MeteoController(),
            WhoIsHomeController(),
        )
    else:
        jobs = (
            FileOutputDisplay(0.1),
            Tuner(),
            KeyboardController(),
            AstroController(),
            MeteoController(),
            WhoIsHomeController(),
        )

    threads = [Thread(target=x.run) for x in jobs]

    try:
        [t.start() for t in threads]
        radio.run()
    except KeyboardInterrupt:
        pass
    finally:
        for i in reversed(range(len(jobs))):
            if threads[i].is_alive():
                radio.bus.send_event(jobs[i].CODE, EVENT_EXIT, True)

        for i in reversed(range(len(jobs))):
            if threads[i].is_alive():
                threads[i].join()

        print("RADIO BYE")
