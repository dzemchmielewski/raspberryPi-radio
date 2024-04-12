import os
import sys
import time
from abc import ABC, abstractmethod
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../."))
from oled.picture_creator import PictureCreator
from entities import TunerStatus, Status
from PIL import Image, ImageDraw, ImageFont


class ShortLifeWindow(ABC):

    def __init__(self, life_span=3 * 1_000):
        self.start = ShortLifeWindow.now()
        self.life_span = life_span

    @staticmethod
    def now():
        return round(time.time() * 1_000)

    @abstractmethod
    def is_completed(self):
        pass

    @abstractmethod
    def draw(self, picture_creator):
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
        else: # self.status == TunerStatus.UNKNOWN
            self.text = ["Już, moment...", ""]

    def is_completed(self):
        return (self.status != TunerStatus.TUNING
                and ShortLifeWindow.now() > (self.start + self.life_span))

    def draw(self, picture_creator):
        # print("[" + "{:%Y-%m-%d %H:%M:%S.%f}".format(datetime.now()) + "][STATUS_WINDOW] " + str(self.text))
        return picture_creator.tuner_status(DisplayManager.WIDTH - 10, self.text)


class DisplayManager:
    WIDTH = 128
    HEIGHT = 96

    def __init__(self):
        self.creator = PictureCreator()
        self.windows = []
        self.station_code = "[]"


    def welcome(self):
        pass

    def volume(self, event):
        pass

    def tuner_status(self, event):
        self.station_code = "[" + event.station.code + "]"
        self.windows = [x for x in self.windows if not x.is_completed() and not isinstance(x, TunerStatusWindow)]
        self.windows += [TunerStatusWindow(event)]

    def display(self):
        main = Image.new('L', (self.WIDTH, self.HEIGHT), 0)

        main.paste(self.creator.top_bar(DisplayManager.WIDTH, station=self.station_code), (0, 0))
        main.paste(self.creator.time(DisplayManager.WIDTH), (0, 30))

        self.windows = [x for x in self.windows if not x.is_completed()]
        for w in self.windows:
            window_image = w.draw(self.creator)
            main.paste(window_image, (5, 35))

        # TODO: $ curl https://api.sunrisesunset.io/json?lat=53.023664\&lng=18.592512\&timezone=CEST\&date=2024-04-12

        # self.text(draw, "Test dzem", 18, 10)
        # self.time(draw)
        # self.frame(draw)

        # if self.volume_event is not None and self.temporary_volume_counter <= 6:
        #   self.temporary_volume_counter += 1
        #  self.text(draw, str(self.volume_event.current_status.volume) + "%", 15, 60)

        return main


if __name__ == "__main__":
    manager = DisplayManager()
    image = manager.display()
    image = image.point(lambda p: p * 16)
    # image.show()
    image.save("out.bmp")
