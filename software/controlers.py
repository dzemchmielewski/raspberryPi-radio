#!/usr/bin/python
import json
from datetime import date, timedelta, datetime

import requests
from alsaaudio import Mixer

from bus import Bus
from configuration import STATIONS, RT_CURRENT_STATION, VISUALCROSSING_URL, VISUALCROSSING_TOKEN
from entities import RadioItem, VolumeStatus, VolumeEvent, STATION_CONTROLLER_LOG, VOLUME_CONTROLLER_LOG, RECOGNIZE_CONTROLLER_LOG, \
    now, AstroData, ASTRO_CONTROLLER_LOG, DUMMY_CONTROLLER_LOG, METEO_CONTROLLER_LOG, MeteoData, \
    HOUR
from hardware import RotaryEncoder, RotaryButton, Button


class AbstractStationController(RadioItem):
    CODE = "station_ctrl"
    EVENT_STATION = "station"

    def __init__(self):
        super(AbstractStationController, self).__init__(Bus(STATION_CONTROLLER_LOG, AbstractStationController.CODE))
        self.stations_count = len(STATIONS)
        saved_station = self.bus.get(RT_CURRENT_STATION)
        if saved_station is None:
            self.current_station = 0
            self.bus.set(RT_CURRENT_STATION, self.current_station)
        else:
            self.current_station = saved_station
        self.bus.send_manager_event(AbstractStationController.EVENT_STATION, self.current_station)

    def rotated(self, direction):
        if direction == RotaryEncoder.DIRECTION_RIGHT:
            if self.current_station + 1 < self.stations_count:
                self.current_station = self.current_station + 1
            else:
                self.current_station = 0
            self.bus.send_manager_event(AbstractStationController.EVENT_STATION, self.current_station)
        else:  # direction == RotaryEncoder.DIRECTION_LEFT
            if self.current_station - 1 >= 0:
                self.current_station = self.current_station - 1
            else:
                self.current_station = self.stations_count - 1
            self.bus.send_manager_event(AbstractStationController.EVENT_STATION, self.current_station)
        self.bus.set(RT_CURRENT_STATION, self.current_station)

    def loop(self):
        pass

    def exit(self):
        pass


class AbstractVolumeController(RadioItem):
    CODE = "volume_ctrl"
    EVENT_VOLUME = "volume"
    DELTA = 3

    def __init__(self):
        super(AbstractVolumeController, self).__init__(Bus(VOLUME_CONTROLLER_LOG, AbstractVolumeController.CODE))
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
        # self.bus.log("ROTATION: {}, mixer: {} ({})".format(direction, self.mixer.getvolume()[0], self.mixer.getmute()[0]))
        status = VolumeStatus(self.mixer.getvolume()[0], self.mixer.getmute()[0])

        if direction == RotaryEncoder.DIRECTION_RIGHT:
            new_status = VolumeStatus(self.calculate_volume(self.DELTA), 0)
            if status.volume == 0:
                new_status.is_muted = 0
            self.bus.send_manager_event(AbstractVolumeController.EVENT_VOLUME, VolumeEvent(status, new_status))
        else:
            new_status = VolumeStatus(self.calculate_volume(-self.DELTA), 0)
            if new_status.volume == 0:
                new_status.is_muted = 1
            self.bus.send_manager_event(AbstractVolumeController.EVENT_VOLUME, VolumeEvent(status, new_status))

        self.mixer.setvolume(new_status.volume)
        if status.is_muted != new_status.is_muted:
            self.mixer.setmute(new_status.is_muted)

    def clicked(self):
        # self.bus.log("CLICKED, mixer: {} ({})".format(self.mixer.getvolume()[0], self.mixer.getmute()[0]))
        status = VolumeStatus(self.mixer.getvolume()[0], self.mixer.getmute()[0])
        new_status = VolumeStatus(status.volume, (status.is_muted + 1) % 2)
        if new_status.is_muted:
            self.bus.send_manager_event(AbstractVolumeController.EVENT_VOLUME, VolumeEvent(status, new_status))
        else:
            # if unmute when volume is 0
            if new_status.volume == 0:
                # then set minimal volume:
                new_status.volume = self.DELTA
            self.bus.send_manager_event(AbstractVolumeController.EVENT_VOLUME, VolumeEvent(status, new_status))
        self.mixer.setmute(new_status.is_muted)
        if status.volume != new_status.volume:
            self.mixer.setvolume(new_status.volume)

    def loop(self):
        pass

    def exit(self):
        pass


class StationController(AbstractStationController):
    def __init__(self, pin_left, pin_right):
        super(StationController, self).__init__()
        self.encoder = RotaryEncoder(pin_left, pin_right, self.rotated)


class VolumeController(AbstractVolumeController):
    def __init__(self, pin_left, pin_right, pin_click):
        super(VolumeController, self).__init__()
        self.encoder = RotaryEncoder(pin_left, pin_right, self.rotated)
        self.button = RotaryButton(pin_click, self.clicked)


class RecognizeController(RadioItem):
    CODE = "recognize_ctrl"
    EVENT_RECOGNIZE = "recognize"

    def __init__(self, pin):
        super(RecognizeController, self).__init__(Bus(RECOGNIZE_CONTROLLER_LOG, RecognizeController.CODE))
        self.button = Button(pin, self.clicked)

    def clicked(self):
        self.bus.send_manager_event(RecognizeController.EVENT_RECOGNIZE, True)

    def loop(self):
        pass

    def exit(self):
        pass


class AstroController(RadioItem):
    CODE = "astro_ctrl"
    EVENT_ASTRO_DATA = "astro_data"

    def __init__(self):
        super(AstroController, self).__init__(Bus(ASTRO_CONTROLLER_LOG, AstroController.CODE), 2)
        self.broadcasted_for_date = None

    @staticmethod
    def pt(time_str):
        if time_str is not None:
            return datetime.strptime(time_str, "%H:%M:%S")
        return None

    def call4data(self, day: date):
        try:
            d_from = (day - timedelta(days=1)).strftime("%Y-%m-%d")
            d_to = (day + timedelta(days=5)).strftime("%Y-%m-%d")
            self.bus.log("External call: " + d_from + " - " + d_to)

            request = (VISUALCROSSING_URL
                       + "/" + d_from + "/" + d_to
                       + "?unitGroup=metric&key=" + VISUALCROSSING_TOKEN
                       + "&contentType=json&elements=datetime,moonphase,sunrise,sunset,moonrise,moonset")
            text = requests.get(request).text

            response = json.loads(text)

            for day in response["days"]:
                data = AstroData(datetime.strptime(day["datetime"], "%Y-%m-%d").date(),
                                 self.pt(day.get("sunrise", None)), self.pt(day.get("sunset", None)),
                                 self.pt(day.get("moonrise", None)), self.pt(day.get("moonset", None)),
                                 day.get("moonphase", None))
                self.bus.set(day["datetime"], data)
            self.bus.log("External call completed (" + str(len(response["days"])) + " datasets saved).")

        except requests.exceptions.HTTPError as e:
            self.bus.log(str(e))
        except requests.exceptions.ConnectionError as e:
            self.bus.log(str(e))
        except requests.exceptions.Timeout as e:
            self.bus.log(str(e))
        except requests.exceptions.RequestException as e:
            self.bus.log(str(e))

    def loop(self):
        today = date.today()

        if self.broadcasted_for_date is None or self.broadcasted_for_date != today:
            requested_day = today.strftime("%Y-%m-%d")
            if (astro_data := self.bus.get(requested_day)) is None:
                self.call4data(today)
                astro_data = self.bus.get(requested_day)
            self.bus.send_manager_event(AstroController.EVENT_ASTRO_DATA, astro_data)
            self.broadcasted_for_date = today
        # TODO: clean outdated astro information

    def exit(self):
        pass


class MeteoController(RadioItem):
    CODE = "meteo_ctrl"
    EVENT_METEO_DATA = "meteo_data"

    def __init__(self):
        super(MeteoController, self).__init__(Bus(METEO_CONTROLLER_LOG, MeteoController.CODE), 2)
        self.last_broadcasted = None
        self.data = None
        self.broadcast_period = 0.5 * HOUR

    def call4data(self):
        try:
            self.bus.log("External call")
            request = (VISUALCROSSING_URL
                       + "?unitGroup=metric&key=" + VISUALCROSSING_TOKEN
                       + "&contentType=json")
            response = json.loads(requests.get(request).text)
            current_cond = response["currentConditions"]
            self.data = MeteoData(
                datetime.fromtimestamp(current_cond.get("datetimeEpoch", None)),
                response.get("description", None),
                current_cond.get("icon", None),
                current_cond.get("temp", None),
                current_cond.get("pressure", None),
                current_cond.get("conditions", None))

            self.bus.log("External call completed")

        except requests.exceptions.HTTPError as e:
            self.bus.log(str(e))
        except requests.exceptions.ConnectionError as e:
            self.bus.log(str(e))
        except requests.exceptions.Timeout as e:
            self.bus.log(str(e))
        except requests.exceptions.RequestException as e:
            self.bus.log(str(e))

    def loop(self):
        current_time = now()
        if self.last_broadcasted is None or current_time > self.last_broadcasted + self.broadcast_period:
            self.call4data()
            self.bus.send_manager_event(MeteoController.EVENT_METEO_DATA, self.data)
            self.last_broadcasted = current_time

    def exit(self):
        pass


class DummyController(RadioItem):
    CODE = "dummy_ctrl"
    EVENT_DUMMY = "dummy"

    def __init__(self, *pins):
        super(DummyController, self).__init__(Bus(DUMMY_CONTROLLER_LOG, DummyController.CODE))
        self.buttons = []
        for pin in pins:
            self.buttons.append(Button(pin, self.clicked))

    def clicked(self):
        self.bus.send_manager_event(DummyController.EVENT_DUMMY, True)

    def loop(self):
        pass

    def exit(self):
        pass
