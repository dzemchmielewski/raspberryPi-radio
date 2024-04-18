import datetime
import os
import sys
import time
from abc import ABC, abstractmethod

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../."))
from oled.assets import Assets
from configuration import SPLASH_SCREEN_DISPLAY, STATIONS
from oled.picture_creator import PictureCreator
from entities import TunerStatus, Status, RecognizeStatus, RecognizeState, now, AstroEvent, AstroDay
from PIL import Image, ImageDraw, ImageEnhance


class ShortLifeWindow(ABC):

    def __init__(self, life_span=3 * 1_000):
        self.start = now()
        self.life_span = life_span

    def is_life_span_passed(self):
        return now() > (self.start + self.life_span)

    @abstractmethod
    def is_completed(self) -> bool:
        pass

    @abstractmethod
    def draw(self, picture_creator) -> Image:
        pass


class TunerStatusWindow(ShortLifeWindow):

    def __init__(self, status: Status):
        super(TunerStatusWindow, self).__init__()
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

    def draw(self, picture_creator) -> Image:
        return picture_creator.text_window(DisplayManager.WIDTH - 10, tuple(self.text), tuple([12, 36]))


class RecognizeWindow(ShortLifeWindow):
    def __init__(self, status: RecognizeStatus):
        super(RecognizeWindow, self).__init__(life_span=10 * 1_000)
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

    def draw(self, picture_creator) -> Image:
        return picture_creator.text_window(DisplayManager.WIDTH - 10, tuple(self.text), tuple(self.size))


class SplashScreenWindow(ShortLifeWindow):

    def __init__(self):
        super(SplashScreenWindow, self).__init__(life_span=SPLASH_SCREEN_DISPLAY)

    def is_completed(self) -> bool:
        return self.is_life_span_passed()

    def draw(self, picture_creator) -> Image:
        return picture_creator.splash_screen(DisplayManager.WIDTH, DisplayManager.HEIGHT)


class AstroWindow:
    def __init__(self, astro_event: AstroEvent):
        self.astro_event = astro_event

    def time(self, time:datetime) -> str:
        if time is not None:
            return time.strftime("%H:%M")
        return "--:--"

    def draw(self, width, height, picture_creator) -> Image:
        result = Image.new('L', (width, height), PictureCreator.C_BLACK)

        sun = Image.open(Assets.moonset).convert('L')
        enh = ImageEnhance.Brightness(sun)
        sun = enh.enhance(0.04)

        result.paste(sun, (0,1))

        text = [self.time(self.astro_event.today.sunrise)]

        time = picture_creator.text_window(width, tuple(text), tuple([20]), vertical_space=5, horizontal_space=0, is_frame=False, font_path=Assets.font_path, debug=True)

        result.paste(time, (round((width - time.size[0]) / 2), sun.size[1] + 1))
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

    def draw(self, picture_creator: PictureCreator, margin = 8):
        result = Image.new('L', (self.width, self.height), PictureCreator.C_BLACK)
        draw = ImageDraw.Draw(result)
        # PictureCreator.__frame__(draw, (width, height), fill=PictureCreator.C_BLACK + 5)

        # upper vertical line:
        draw.line([(self.x_up, self.start_y + margin), (self.x_up, self.y_middle)], fill=PictureCreator.C_WHITE)
        # lower vertical line:
        draw.line([(self.x_low, self.y_middle), (self.x_low, self.end_y - margin)], fill=PictureCreator.C_WHITE)
        # horizontal line in a half:
        draw.line([(margin, self.y_middle), (self.end_x - margin, self.y_middle)], fill=PictureCreator.C_WHITE)

        q1 = self.q1(picture_creator)
        y = round((((self.y_middle - self.start_y) - q1.size[1]) / 2))
        result.paste(q1, (self.start_x, y))

        q3 = self.q3(picture_creator)
        y = round((((self.y_middle - self.start_y) - q3.size[1]) / 2))
        result.paste(q3, (self.start_x, y + self.y_middle + 1))

        q4 = self.q4(picture_creator)
        y = round((((self.end_y - self.y_middle) - q4.size[1]) / 2))
        result.paste(q4, (self.x_low + 1, y + self.y_middle))

        return result

    def q1(self, picture_creator: PictureCreator):
        # Quarter 1 - display date
        now = datetime.datetime.now()
        text = [picture_creator.display_week_day(now.weekday()) + ", " + str(now.day), picture_creator.display_month(now.month)]
        return picture_creator.text_window(self.x_up - self.start_x, tuple(text), tuple([16, 34]), is_frame = False, vertical_space=2, fill=PictureCreator.C_BLACK)

    def q3(self, picture_creator: PictureCreator):
        # Quarter 3 - astrological information
        return self.astro_window.draw(self.x_low - self.start_x, self.end_y - self.y_middle, picture_creator)

    def q4(self, picture_creator: PictureCreator):
        # Quarter 4 - display time
        text = [datetime.datetime.now().strftime("%H:%M")]
        return picture_creator.text_window(self.end_x - self.x_low, tuple(text), tuple([34]), is_frame = False, fill=PictureCreator.C_BLACK)


class DisplayManager:
    WIDTH = 128
    HEIGHT = 96

    def __init__(self):
        self.creator = PictureCreator()
        self.splash = SplashScreenWindow()
        self.windows = []
        self.station = None
        self.astro_window = AstroWindow(AstroEvent())
        self.main_window = MainWindow(DisplayManager.WIDTH, DisplayManager.HEIGHT - 13, self.astro_window)

    def welcome(self):
        pass

    def volume(self, event):
        pass

    def recognize_status(self, event):
        self.add_window(RecognizeWindow(event))

    def tuner_status(self, event):
        self.station = event.station
        self.add_window(TunerStatusWindow(event))

    def astro(self, event):
        self.astro_window.astro_event = event

    def add_window(self, window):
        self.windows = [x for x in self.windows if not x.is_completed() and not isinstance(x, type(window))]
        self.windows += [window]

    def display(self):
        self.windows = [x for x in self.windows if not x.is_completed()]

        if self.splash is not None:
            if self.splash.is_completed():
                self.splash = None
            else:
                return self.splash.draw(self.creator)

        main = Image.new('L', (self.WIDTH, self.HEIGHT), 0)
        main.paste(self.creator.top_bar2(DisplayManager.WIDTH, 13, station=self.station), (0, 0))
        #main.paste(self.creator.time(DisplayManager.WIDTH), (0, 30))
        main.paste(self.main_window.draw(self.creator), (0, 13))

        #main.paste(self.astro_window.draw(self.creator), (0, 78))

        for w in self.windows:
            window_image = w.draw(self.creator)
            x = round((DisplayManager.WIDTH - window_image.size[0]) / 2)
            y = round((DisplayManager.HEIGHT - window_image.size[1]) / 2)
            main.paste(window_image, (x, y))

        return main


if __name__ == "__main__":
    manager = DisplayManager()

    manager.splash = None
    manager.station = STATIONS[2]
    manager.astro(AstroEvent(AstroDay(datetime.time(5, 31), datetime.time(19, 3)), None))

#    while True:
    if 1 == 1:
        image = manager.display()
        image = image.point(lambda p: p * 16)
        # image.show()
        image.save("out.bmp")
        time.sleep(0.1)
