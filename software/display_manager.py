import datetime
import os
import sys
import time
from abc import ABC, abstractmethod

import drawing

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../."))
from assets import Assets
from configuration import SPLASH_SCREEN_DISPLAY, STATIONS, DISPLAY_WIDTH, DISPLAY_HEIGHT
from entities import TunerStatus, Status, RecognizeStatus, RecognizeState, now, AstroData, time_f
from PIL import Image, ImageDraw, ImageEnhance


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
                    self.status.json["result"]["artist"],
                    self.status.json["result"]["title"],
                    self.status.json["result"]["album"],
                    self.status.json["result"]["release_date"]]

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


class AstroWindow:
    def __init__(self):
        self.astro_data = None

    def draw(self, width, height) -> Image:
        result = Image.new('L', (width, height), drawing.C_BLACK)

        sun = Image.open(Assets.sunrise).convert('L')
        enh = ImageEnhance.Brightness(sun)
        sun = enh.enhance(0.04)

        result.paste(sun, (0,1))

        next_day = chr(8594)
        prev_day = chr(8592)

        if self.astro_data is not None:
            text = [time_f(self.astro_data.sunrise)]
        else:
            text = [prev_day + time_f(None)]

        time_img = drawing.text_window(width, tuple(text), tuple([20]), vertical_space=5, horizontal_space=0, is_frame=False, font_path=Assets.font_path, debug=True)

        result.paste(time_img, (round((width - time_img.size[0]) / 2), sun.size[1] + 1))
        return result


class MainWindow:
    def __init__(self, width:int, height:int, astro_window: AstroWindow):
        self.astro_window = astro_window

        self.width = width
        self.height = height

        self.start_x = 0
        self.start_y = 0
        self.end_x = self.width
        self.end_y = self.height

        # upper space split: 60% | 40%:
        self.x_up = round((6/10) * self.width)
        # lower space split: 30% | 70%
        self.x_low = round((3/10) * self.width)
        # split horizontaly in half
        self.y_middle = round(self.height / 2)

    def draw(self, margin = 8):
        result = Image.new('L', (self.width, self.height), drawing.C_BLACK)
        draw = ImageDraw.Draw(result)
        # PictureCreator.__frame__(draw, (width, height), fill=drawing.C_BLACK + 5)

        # upper vertical line:
        draw.line([(self.x_up, self.start_y + margin), (self.x_up, self.y_middle)], fill=drawing.C_WHITE)
        # lower vertical line:
        draw.line([(self.x_low, self.y_middle), (self.x_low, self.end_y - margin)], fill=drawing.C_WHITE)
        # horizontal line in a half:
        draw.line([(margin, self.y_middle), (self.end_x - margin, self.y_middle)], fill=drawing.C_WHITE)

        q1 = self.q1()
        y = round((((self.y_middle - self.start_y) - q1.size[1]) / 2))
        result.paste(q1, (self.start_x, y))

        q3 = self.q3()
        y = round((((self.y_middle - self.start_y) - q3.size[1]) / 2))
        result.paste(q3, (self.start_x, y + self.y_middle + 2))

        q4 = self.q4()
        y = round((((self.end_y - self.y_middle) - q4.size[1]) / 2))
        result.paste(q4, (self.x_low + 1, y + self.y_middle))

        return result

    def q1(self):
        # Quarter 1 - display date
        now = datetime.datetime.now()
        text = [drawing.display_week_day(now.weekday()) + ", " + str(now.day), drawing.display_month(now.month)]
        return drawing.text_window(self.x_up - self.start_x, tuple(text), tuple([16, 34]), is_frame = False, vertical_space=2, fill=drawing.C_BLACK)

    def q3(self):
        # Quarter 3 - astrological information
        return self.astro_window.draw(self.x_low - self.start_x, self.end_y - self.y_middle)

    def q4(self):
        # Quarter 4 - display time
        text = [datetime.datetime.now().strftime("%H:%M")]
        return drawing.text_window(self.end_x - self.x_low, tuple(text), tuple([34]), is_frame = False, fill=drawing.C_BLACK)


class DisplayManager:

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.splash = SplashScreenWindow(width, height)
        self.windows = []
        self.station = None
        self.astro_window = AstroWindow()
        self.main_window = MainWindow(width, height - 13, self.astro_window)

    def volume(self, event):
        pass

    def recognize_status(self, event):
        self.add_window(RecognizeWindow(event, self.width - 10))

    def tuner_status(self, event):
        self.station = event.station
        self.add_window(TunerStatusWindow(event, self.width - 10))

    def astro(self, event: AstroData):
        self.astro_window.astro_data = event

    def new_astro(self):
        today = datetime.date.today()
        if self.astro_window.astro_data is None or self.astro_window.astro_data.day != today:
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
        #main.paste(self.creator.time(self.width), (0, 30))
        main.paste(self.main_window.draw(), (0, 13))

        #main.paste(self.astro_window.draw(), (0, 78))

        for w in self.windows:
            window_image = w.draw()
            x = round((self.width - window_image.size[0]) / 2)
            y = round((self.height - window_image.size[1]) / 2)
            main.paste(window_image, (x, y))

        return main


if __name__ == "__main__":
    manager = DisplayManager(DISPLAY_WIDTH, DISPLAY_HEIGHT)

    manager.splash = None
    manager.station = STATIONS[2]
    manager.astro(AstroData(
        datetime.date.today(),
        datetime.time(5, 31), datetime.time(19, 3),
        datetime.time(19, 17), None,
        0.32))


#    while True:
    if 1 == 1:
        image = manager.display()
        image = image.point(lambda p: p * 16)
        # image.show()
        image.save("out.bmp")
        time.sleep(0.1)
