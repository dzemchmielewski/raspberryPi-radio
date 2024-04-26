#!/usr/bin/python
import json
from datetime import date, timedelta, datetime, time

import requests
from alsaaudio import Mixer

from bus import Bus
from configuration import STATIONS, RT_CURRENT_STATION, ACCUWEATHER_CURRENT_URL, ACCUWEATHER_FORECAST_URL, VISUALCROSSING_URL, \
    VISUALCROSSING_TOKEN
from entities import RadioItem, VolumeStatus, VolumeEvent, STATION_CONTROLLER_LOG, VOLUME_CONTROLLER_LOG, RECOGNIZE_CONTROLLER_LOG, \
    ACCUWEATHER_CONTROLLER_LOG, WeatherEvent, now, AstroData, ASTRO_CONTROLLER_LOG, DUMMY_CONTROLLER_LOG
from hardware import RotaryEncoder, RotaryButton, Button


class AbstractStationController(RadioItem):
    CODE = "station_ctrl"
    EVENT_STATION = "station_up"

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
        #self.bus.log("ROTATION: {}, mixer: {} ({})".format(direction, self.mixer.getvolume()[0], self.mixer.getmute()[0]))
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
        #self.bus.log("CLICKED, mixer: {} ({})".format(self.mixer.getvolume()[0], self.mixer.getmute()[0]))
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
    EVENT_ASTRO_DATA_REQUEST = "astro_data_req"

    def __init__(self):
        super(AstroController, self).__init__(Bus(ASTRO_CONTROLLER_LOG, AstroController.CODE), 2)

    @staticmethod
    def pt(time_str):
        if time_str is not None:
            return datetime.strptime(time_str, "%H:%M:%S")
        return None

    def call4data(self, date: date):
        try:
            d_from = (date - timedelta(days=1)).strftime("%Y-%m-%d")
            d_to = (date + timedelta(days=5)).strftime("%Y-%m-%d")
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
        if (event := self.bus.consume_event(AstroController.EVENT_ASTRO_DATA_REQUEST)) is not None:
            requested_day = event.strftime("%Y-%m-%d")
            if (astro_data := self.bus.get(requested_day)) is None:
                self.call4data(event)
                astro_data = self.bus.get(requested_day)
            self.bus.send_manager_event(AstroController.EVENT_ASTRO_DATA, astro_data)
        #TODO: clean outdated astro information

    def exit(self):
        pass


class DummyController(RadioItem):
    CODE = "dummy_ctrl"
    EVENT_DUMMY = "dummy"

    def __init__(self, *pins):
        super(DummyController, self).__init__(Bus(DUMMY_CONTROLLER_LOG, RecognizeController.CODE))
        self.buttons = []
        for pin in pins:
            self.buttons.append(Button(pin, self.clicked))

    def clicked(self):
        self.bus.send_manager_event(DummyController.EVENT_DUMMY, True)

    def loop(self):
        pass

    def exit(self):
        pass


class AccuweatherController(RadioItem):
    CODE = "accuweather"
    EVENT = "new_weather"

    def __init__(self):
        super(AccuweatherController, self).__init__(Bus(ACCUWEATHER_CONTROLLER_LOG, AccuweatherController.CODE), 2)
        self.last_event: WeatherEvent = None
        self.last_call: int = None
        self.period = 60 * 60 * 1_000
        # self.period = 30 * 1_000

    def loop(self):
        try:

            if self.last_call is None or now() > self.last_call + self.period:

                current = json.loads(requests.get(ACCUWEATHER_CURRENT_URL).text)
                forecast = json.loads(requests.get(ACCUWEATHER_FORECAST_URL).text)
                event = WeatherEvent(current, forecast)
                if self.last_event is None or self.last_event.dates() != event.dates():
                    self.last_event = event
                    self.bus.send_manager_event(AccuweatherController.EVENT, event)
                else:
                    self.bus.log("No changes to the accuweather data.")
                self.last_call = now()

        except requests.exceptions.HTTPError as e:
            self.bus.log(str(e))
        except requests.exceptions.ConnectionError as e:
            self.bus.log(str(e))
        except requests.exceptions.Timeout as e:
            self.bus.log(str(e))
        except requests.exceptions.RequestException as e:
            self.bus.log(str(e))

    def exit(self):
        pass
