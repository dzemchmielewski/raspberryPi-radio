import datetime
import os
import sys
from abc import ABC, abstractmethod

import drawing
import screensavers

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../."))
from configuration import SPLASH_SCREEN_DISPLAY
from entities import TunerStatus, Status, RecognizeStatus, RecognizeState, now, AstroData, VolumeEvent
from PIL import Image, ImageDraw


class ShortLifeWindow(ABC):

    def __init__(self, life_span=3 * 1_000, width: int = 0):
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

    def __init__(self, width, height, stop_time=2 * 1_000):
        self.width = width
        self.height = height
        self.stop_time = stop_time
        self.in_movement = False
        self.move_step = 8
        self.position = 0
        self.last_stop = now()

    @abstractmethod
    def get_strip(self):
        pass

    def draw(self) -> Image:
        strip = self.get_strip()

        if now() > (self.last_stop + self.stop_time):
            self.in_movement = True

        if self.in_movement:
            if self.position + self.width == strip.size[0]:
                self.position = 0

            next_move_step = self.move_step
            for i in range(0, self.move_step):
                if (self.position + (i + 1)) % self.width == 0:
                    next_move_step = i + 1
                    break
            self.position += next_move_step

            if self.position % self.width == 0:
                self.in_movement = False
                self.last_stop = now()

        return strip.crop([self.position, 0, self.position + self.width, strip.size[1]])


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
        super(RecognizeWindow, self).__init__(life_span=10 * 1_000, width=width)
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
        super(MeteoWindow, self).__init__(width, height)

    def get_strip(self):
        # img = Image.open(Assets.weather_icons + "partly-cloudy-night.png").convert('L')
        # img.thumbnail((width, height), Image.Resampling.LANCZOS)
        # result.paste(img, (round((width - img.size[0]) / 2), round((height - img.size[1]) / 2)))
        return Image.new('L', (self.width, self.height), drawing.C_BLACK)


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

        # Quarter 1 - display date
        currently = datetime.datetime.now()
        text = [drawing.display_week_day(currently.weekday()) + ", " + str(currently.day), drawing.display_month(currently.month)]
        q1 = drawing.text_window(self.x_up - self.start_x, tuple(text), tuple([16, 34]), is_frame=False, vertical_space=2,
                                 fill=drawing.C_BLACK)
        y = round((((self.y_middle - self.start_y) - q1.size[1]) / 2))
        result.paste(q1, (self.start_x, y))

        # Quarter 2 - display meteo info
        # frame max size: 50x42
        q2 = self.meteo_window.draw()
        y = round((((self.y_middle - self.start_y) - q2.size[1]) / 2))
        result.paste(q2, (self.x_up + 1, y - 1))

        # Quarter 3 - astrological information
        q3 = self.astro_window.draw()
        y = round((((self.y_middle - self.start_y) - q3.size[1]) / 2))
        result.paste(q3, (self.start_x, y + self.y_middle + 2))

        # Quarter 4 - display time
        text = [datetime.datetime.now().strftime("%H:%M")]
        q4 = drawing.text_window(self.end_x - self.x_low, tuple(text), tuple([34]), is_frame=False, fill=drawing.C_BLACK)
        y = round((((self.end_y - self.y_middle) - q4.size[1]) / 2))
        result.paste(q4, (self.x_low + 1, y + self.y_middle))

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

    def astro(self, event: AstroData):
        self.main_window.astro_window.astro_data = event

    def screensaver(self, event: bool):
        if event:
            self.screensaver_window = screensavers.get_screensaver(self.width, self.height)
        else:
            self.screensaver_window = None

    def new_astro(self):
        today = datetime.date.today()
        if self.main_window.astro_window.astro_data is None or self.main_window.astro_window.astro_data.day != today:
            return today
        return None

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
