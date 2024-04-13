import os
import sys
import time
from abc import ABC, abstractmethod

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../."))
from oled.picture_creator import PictureCreator
from entities import TunerStatus, Status, Station, RecognizeStatus, RecognizeState
from PIL import Image


class ShortLifeWindow(ABC):

    def __init__(self, life_span=3 * 1_000):
        self.start = ShortLifeWindow.now()
        self.life_span = life_span

    def is_life_span_passed(self):
        return ShortLifeWindow.now() > (self.start + self.life_span)

    @staticmethod
    def now():
        return round(time.time() * 1_000)

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
        else: # self.status == TunerStatus.UNKNOWN
            self.text = ["Już, moment..."]

    def is_completed(self) -> bool:
        return (self.status != TunerStatus.TUNING
                and self.is_life_span_passed())

    def draw(self, picture_creator) -> Image:
        return picture_creator.text_window(DisplayManager.WIDTH - 10, self.text, [12,36])


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
        return picture_creator.text_window(DisplayManager.WIDTH - 10, self.text, self.size)


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

    def recognize_status(self, event):
        self.add_window(RecognizeWindow(event))

    def tuner_status(self, event):
        self.station_code = "[" + event.station.code + "]"
        self.add_window(TunerStatusWindow(event))

    def add_window(self, window):
        self.windows = [x for x in self.windows if not x.is_completed() and not isinstance(x, type(window))]
        self.windows += [window]


    def display(self):
        main = Image.new('L', (self.WIDTH, self.HEIGHT), 0)

        main.paste(self.creator.top_bar(DisplayManager.WIDTH, station=self.station_code), (0, 0))
        main.paste(self.creator.time(DisplayManager.WIDTH), (0, 30))

        self.windows = [x for x in self.windows if not x.is_completed()]
        for w in self.windows:
            window_image = w.draw(self.creator)
            x = round((DisplayManager.WIDTH - window_image.size[0]) / 2)
            y = round((DisplayManager.HEIGHT - window_image.size[1]) / 2)
            main.paste(window_image, (x, y))

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

    #manager.tuner_status(Status(TunerStatus.UNKNOWN, Station("Radio Nowy Świat", "RNS", "http://stream.rcs.revma.com/ypqt40u0x1zuv")))
    manager.tuner_status(Status(TunerStatus.TUNING, Station("Radio Nowy Świat", "RNS", "http://stream.rcs.revma.com/ypqt40u0x1zuv")))
    #manager.tuner_status(Status(TunerStatus.PLAYING, Station("Los 40", "LOS40", "https://25683.live.streamtheworld.com/LOS40.mp3")))

    image = manager.display()
    image = image.point(lambda p: p * 16)
    # image.show()
    image.save("out.bmp")
