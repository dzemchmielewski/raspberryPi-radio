#!/usr/bin/python
import sys
from threading import Thread

from bus import Bus
from configuration import STATIONS
from entities import RADIO_MANAGER_CODE, Status, EVENT_EXIT, RadioItem, TunerStatus, RADIO_LOG
from controlers import StationController, VolumeController
from tests.manual_controllers import ManualStationController
from outputs import Tuner, LEDOutput


class RadioManager(RadioItem):

    def __init__(self):
        super(RadioManager, self).__init__(Bus(RADIO_LOG, RADIO_MANAGER_CODE))
        self.current_station = None

    def loop(self):
        if (event := self.bus.consume_event(StationController.EVENT_STATION_UP)) is not None:
            self.current_station = event
            self.bus.send_event(LEDOutput.CODE, LEDOutput.EVENT_STATUS, Status(TunerStatus.UNKNOWN, STATIONS[event]))
            self.bus.send_event(Tuner.CODE, Tuner.EVENT_STATION, STATIONS[event])

        if (event := self.bus.consume_event(StationController.EVENT_STATION_DOWN)) is not None:
            self.current_station = event
            self.bus.send_event(LEDOutput.CODE, LEDOutput.EVENT_STATUS, Status(TunerStatus.UNKNOWN, STATIONS[event]))
            self.bus.send_event(Tuner.CODE, Tuner.EVENT_STATION, STATIONS[event])

        if (event := self.bus.consume_event(StationController.EVENT_STATION_SET)) is not None:
            self.current_station = event
            self.bus.send_event(LEDOutput.CODE, LEDOutput.EVENT_STATUS, Status(TunerStatus.UNKNOWN, STATIONS[event]))
            self.bus.send_event(Tuner.CODE, Tuner.EVENT_STATION, STATIONS[event])

        if (event := self.bus.consume_event(VolumeController.EVENT_VOLUME_UP)) is not None:
            pass
        if (event := self.bus.consume_event(VolumeController.EVENT_VOLUME_DOWN)) is not None:
            pass
        if (event := self.bus.consume_event(VolumeController.EVENT_VOLUME_MUTE)) is not None:
            pass
        if (event := self.bus.consume_event(VolumeController.EVENT_VOLUME_UNMUTE)) is not None:
            pass

        if (event := self.bus.consume_event(Tuner.EVENT_PLAY_STATUS)) is not None:
            self.bus.send_event(LEDOutput.CODE, LEDOutput.EVENT_STATUS, Status(event, STATIONS[self.current_station]))


if __name__ == "__main__":

    radio = RadioManager()

    isPi = True
    n = len(sys.argv)
    if n > 1 and sys.argv[1] == "local":
        isPi = False

    if isPi:
        jobs = (
            Tuner(),
            LEDOutput(),
            StationController(),
            VolumeController()
        )
    else:
        jobs = (
            Tuner(),
            LEDOutput(),
            ManualStationController(),
            #ManualVolumeController()
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
