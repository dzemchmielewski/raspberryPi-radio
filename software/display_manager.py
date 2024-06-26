import datetime
import os
import sys
from abc import ABC, abstractmethod

import drawing
import screensavers

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../."))
from configuration import SPLASH_SCREEN_DISPLAY, SELECT_STATION_COMMIT_TIME, STATIONS
from entities import TunerStatus, Status, RecognizeStatus, RecognizeState, now, AstroData, VolumeEvent, MeteoData, SECOND
from PIL import Image, ImageDraw


class ShortLifeWindow(ABC):

    def __init__(self, life_span=3 * SECOND, width: int = 0):
        self.start = now()
        self.width = width
        self.life_span = life_span

    def is_life_span_passed(self):
        return now() > (self.start + self.life_span)

    @abstractmethod
    def is_completed(self) -> bool:
        pass

    @abstractmethod
    def draw(self) -> Image:
        pass


class SlideWindow(ABC):

    DIRECTION_LEFT = 'L'
    DIRECTION_UP = 'U'

    def __init__(self, width: int, height: int, stop_time=2 * SECOND, initial_delay: int = 0, direction=DIRECTION_LEFT, debug=False):
        self.width = width
        self.height = height
        self.stop_time = stop_time
        self.initial_delay = initial_delay
        self.direction = direction
        self.in_movement = False
        self.move_step = 8
        self.position = 0
        self.last_stop = now()
        self.debug = debug


    @abstractmethod
    def get_strip(self):
        pass

    def draw(self) -> Image:
        strip = self.get_strip()

        if self.direction == self.DIRECTION_LEFT:
            related_size = self.width
            related_size_index = 0
        elif self.direction == self.DIRECTION_UP:
            related_size = self.height
            related_size_index = 1
        else:
            raise Exception("Unknown direction value: {}".format(self.direction))

        if self.debug:
            print("width: {}, height: {}".format(self.width, self.height))

        if isinstance(self.stop_time, list):
            if strip.size[related_size_index]//related_size == 1:
                stop_time = self.stop_time[(self.position // related_size)]
            else:
                stop_time = self.stop_time[(self.position // related_size) % ((strip.size[related_size_index]//related_size) - 1)]
        else:
            stop_time = self.stop_time

        if self.debug:
            print("{} :position , stop_time: {}, related_size: {} / {}".format(self.position, stop_time, strip.size[related_size_index], related_size))

        if now() > (self.last_stop + stop_time + self.initial_delay):
            self.initial_delay = 0
            self.in_movement = True

        if strip.size[related_size_index] > related_size and self.in_movement:
            if self.position + related_size == strip.size[related_size_index]:
                self.position = 0

            next_move_step = self.move_step
            for i in range(0, self.move_step):
                if (self.position + (i + 1)) % related_size == 0:
                    next_move_step = i + 1
                    break
            self.position += next_move_step

            if self.position % related_size == 0:
                self.in_movement = False
                self.last_stop = now()

        if related_size_index == 0:
            return strip.crop([self.position, 0, self.position + self.width, strip.size[1]])
        else:
            return strip.crop([0, self.position, strip.size[0],  self.position + self.height])


class TunerStatusWindow(ShortLifeWindow):

    def __init__(self, status: Status, width: int):
        super(TunerStatusWindow, self).__init__(width=width)
        self.status = status.status
        self.text = []
        if self.status == TunerStatus.TUNING:
            self.text = ["Próbujemy...", status.station.name]
        elif self.status == TunerStatus.PLAYING:
            self.text = ["To słuchamy!", status.station.name]
        else:  # self.status == TunerStatus.UNKNOWN
            self.text = ["Już, moment..."]

    def is_completed(self) -> bool:
        return (self.status != TunerStatus.TUNING
                and self.is_life_span_passed())

    def draw(self) -> Image:
        return drawing.text_window(self.width, tuple(self.text), tuple([12, 36]))


class SelectStationWindow(ShortLifeWindow):

    def __init__(self, station: int, width: int):
        super(SelectStationWindow, self).__init__(width=width, life_span=SELECT_STATION_COMMIT_TIME)
        length = len(STATIONS)
        start = ((station - 2) + length) % length
        self.text = []
        for i in range(start, start + (2*2) + 1):
            self.text.append(STATIONS[i % length].name)

    def is_completed(self) -> bool:
        return self.is_life_span_passed()

    def draw(self) -> Image:
        return drawing.select_station(self.width, tuple(self.text))


class TunerInfoWindow(ShortLifeWindow):

    def __init__(self, info: str, width: int):
        super(TunerInfoWindow, self).__init__(width=width, life_span=10 * SECOND)
        if " - " in info:
            self.text = info.split(" - ")
        else:
            self.text = drawing.split(info, 16, one_frame_only = True)

    def is_completed(self) -> bool:
        return self.is_life_span_passed()

    def draw(self) -> Image:
        return drawing.text_window(self.width, tuple(self.text), tuple([30] * len(self.text)))


class VolumeWindow(ShortLifeWindow):

    def __init__(self, volume: VolumeEvent, width: int):
        super(VolumeWindow, self).__init__(width=width)
        self.volume = volume

    def is_completed(self) -> bool:
        return self.is_life_span_passed()

    def draw(self) -> Image:
        return drawing.volume_window(self.width, 40, self.volume.current_status.volume, mute=self.volume.current_status.is_muted)


class RecognizeWindow(ShortLifeWindow):
    def __init__(self, status: RecognizeStatus, width):
        super(RecognizeWindow, self).__init__(life_span=10 * SECOND, width=width)
        self.status = status
        self.text = []
        self.size = [16, 16, 14, 12]
        if self.status.state == RecognizeState.CONNECTING:
            self.text = ["Ej, co to gra..?"]
        if self.status.state == RecognizeState.RECORDING:
            self.text = ["Ej, co to gra..?", "... nagrajmy kawałek..."]
        if self.status.state == RecognizeState.QUERYING:
            self.text = ["Ej, co to gra..?", "- pytanie do eksperta..."]
        if self.status.state == RecognizeState.DONE:
            if self.status.json["status"] == "error":
                self.text = ["Ej, co to gra..?", "coś poszło bardzo nie tak!"]
            elif self.status.json["status"] == "success" and self.status.json["result"] is None:
                self.text = ["Ej, co to gra..?", "- nie mam pojęcia!"]
            else:  # self.status.json["status"] == "success" and self.status.json["result"] is not None
                self.text = [
                    self.status.json["result"].get("artist", ""),
                    self.status.json["result"].get("title", ""),
                    self.status.json["result"].get("album", ""),
                    self.status.json["result"].get("release_date", "")]

    def is_completed(self) -> bool:
        return self.status.state == RecognizeState.DONE and self.is_life_span_passed()

    def draw(self) -> Image:
        return drawing.text_window(self.width, tuple(self.text), tuple(self.size))


class SplashScreenWindow(ShortLifeWindow):

    def __init__(self, width: int, height: int):
        super(SplashScreenWindow, self).__init__(life_span=SPLASH_SCREEN_DISPLAY, width=width)
        self.height = height

    def is_completed(self) -> bool:
        return self.is_life_span_passed()

    def draw(self) -> Image:
        return drawing.splash_screen(self.width, self.height)


class AstroWindow(SlideWindow):
    def __init__(self, width: int, height: int):
        super(AstroWindow, self).__init__(width, height)
        self.astro_data = None

    def get_strip(self):
        return drawing.create_astro_strip(self.width, self.height, self.astro_data)


class MeteoWindow(SlideWindow):
    def __init__(self, width: int, height: int):
        super(MeteoWindow, self).__init__(width, height, initial_delay=0.5 * SECOND, stop_time=3 * SECOND)
        self.meteo_data: MeteoData = None

    def get_strip(self):
        return drawing.create_meteo_strip(self.width, self.height, self.meteo_data)


class DateWindow(SlideWindow):
    def __init__(self, width: int, height: int):
        super(DateWindow, self).__init__(width, height, initial_delay=0.7 * SECOND, stop_time=[12 * SECOND, 3 * SECOND, 3 * SECOND], direction=SlideWindow.DIRECTION_UP)
        self.description = None

    def get_strip(self):
        currently = datetime.datetime.now()
        text = [drawing.display_week_day(currently.weekday()) + ", " + str(currently.day), drawing.display_month(currently.month)]
        return drawing.create_date_strip(self.width, self.height, tuple(text), self.description)


class TimeWindow(SlideWindow):
    def __init__(self, width: int, height: int):
        super(TimeWindow, self).__init__(width, height, stop_time=[15 * SECOND, 2 * SECOND, 2 * SECOND], direction=SlideWindow.DIRECTION_UP)
        self.holidays = []

    def get_strip(self):
        text = [datetime.datetime.now().strftime("%H:%M")]
        return drawing.create_time_strip(self.width, self.height, tuple(text), tuple(self.holidays))


class MainWindow:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        self.start_x = 0
        self.start_y = 0
        self.end_x = self.width
        self.end_y = self.height

        # upper space split: 60% | 40%:
        self.x_up = round((6 / 10) * self.width)
        # lower space split: 30% | 70%
        self.x_low = round((3 / 10) * self.width)
        # split horizontally in half
        self.y_middle = round(self.height / 2)

        self.astro_window = AstroWindow(self.x_low - self.start_x, self.end_y - self.y_middle)
        self.meteo_window = MeteoWindow(self.end_x - self.x_up, self.y_middle - self.start_y)
        self.date_window = DateWindow(self.x_up - self.start_x, self.y_middle - self.start_y)
        self.time_window = TimeWindow(self.end_x - self.x_low, self.end_y - self.y_middle)

    def draw(self, margin=8):
        result = Image.new('L', (self.width, self.height), drawing.C_BLACK)
        draw = ImageDraw.Draw(result)
        # PictureCreator.__frame__(draw, (width, height), fill=drawing.C_BLACK + 5)

        # upper vertical line:
        draw.line([(self.x_up, self.start_y + margin), (self.x_up, self.y_middle)], fill=drawing.C_WHITE)
        # lower vertical line:
        draw.line([(self.x_low, self.y_middle), (self.x_low, self.end_y - margin)], fill=drawing.C_WHITE)
        # horizontal line in a half:
        draw.line([(margin, self.y_middle), (self.end_x - margin, self.y_middle)], fill=drawing.C_WHITE)

        # Quarter 1 - display date & weather description
        # 77x43
        q1 = self.date_window.draw()
        y = round((((self.y_middle - self.start_y) - q1.size[1]) / 2))
        result.paste(q1, (self.start_x, y))

        # Quarter 2 - meteo info
        # frame max size: 50x42
        q2 = self.meteo_window.draw()
        y = round((((self.y_middle - self.start_y) - q2.size[1]) / 2))
        result.paste(q2, (self.x_up + 1, y - 1))

        # Quarter 3 - astrological information
        q3 = self.astro_window.draw()
        y = round((((self.y_middle - self.start_y) - q3.size[1]) / 2))
        result.paste(q3, (self.start_x, y + self.y_middle + 2))

        # Quarter 4 - display time
        q4 = self.time_window.draw()
        y = round((((self.end_y - self.y_middle) - q4.size[1]) / 2))
        result.paste(q4, (self.x_low + 1, y + self.y_middle + 2))

        return result


class DisplayManager:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.splash = SplashScreenWindow(width, height)
        self.windows = []
        self.station = None
        self.screensaver_window = None
        self.main_window = MainWindow(width, height - 13)

    def volume(self, event):
        self.add_window(VolumeWindow(event, self.width - 10))

    def recognize_status(self, event):
        self.add_window(RecognizeWindow(event, self.width - 10))

    def tuner_status(self, event):
        self.station = event.station
        self.add_window(TunerStatusWindow(event, self.width - 10))

    def tuner_play_info(self, event):
        self.add_window(TunerInfoWindow(event, self.width - 10))

    def select_station(self, event):
        self.add_window(SelectStationWindow(event, self.width - 10))

    def astro(self, event: AstroData):
        self.main_window.astro_window.astro_data = event

    def meteo(self, event: MeteoData):
        self.main_window.meteo_window.meteo_data = event
        self.main_window.date_window.description = event.description

    def holiday(self, event: [str]):
        self.main_window.time_window.holidays = event

    def screensaver(self, event: bool):
        if event:
            self.screensaver_window = screensavers.get_screensaver(self.width, self.height)
        else:
            self.screensaver_window = None

    def add_window(self, window):
        self.windows = [x for x in self.windows if not x.is_completed() and not isinstance(x, type(window))]
        self.windows += [window]

    def display(self):
        self.windows = [x for x in self.windows if not x.is_completed()]

        if self.splash is not None:
            if self.splash.is_completed():
                self.splash = None
            else:
                return self.splash.draw()

        main = Image.new('L', (self.width, self.height), 0)
        main.paste(drawing.top_bar2(self.width, 13, station=self.station), (0, 0))
        main.paste(self.main_window.draw(), (0, 13))

        for w in self.windows:
            window_image = w.draw()
            x = round((self.width - window_image.size[0]) / 2)
            y = round((self.height - window_image.size[1]) / 2)
            main.paste(window_image, (x, y))

        if self.screensaver_window is not None:
            self.screensaver_window.draw(main)

        return main


if __name__ == "__main__":
    pass