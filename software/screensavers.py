import math
import random
import time

from PIL import ImageDraw, Image

import drawing
from assets import Assets


def get_screensaver(width: int, height: int):
    return Snake(width, height)


class Screensaver:

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

    def draw(self, img: Image):
        draw = ImageDraw.Draw(img)
        draw.rectangle(((0, 0), (img.size[0] - 1, img.size[1] - 1)), fill=drawing.C_BLACK)


class FadingStars(Screensaver):
    NOT_PROCESSED_YET = -1

    def __init__(self, width: int, height: int, star_size=4):
        super().__init__(width, height)
        self.max_fading_stars = 15
        self.fading_stars = []
        self.star_size = star_size
        self.w = math.ceil(width / self.star_size)
        self.h = math.ceil(height / self.star_size)
        self.matrix = [(x, -1) for x in range(self.w * self.h)]
        self.mordeczka = Image.open(Assets.mordeczka).convert('L')

    def draw(self, img: Image) -> Image:
        img.paste(self.mordeczka, (0, 0))

        # get all possible stars that can blow up
        sample_space = list(filter(lambda x: x[1] == self.NOT_PROCESSED_YET, self.matrix))

        # remove from fading stars the ones that already faded:
        self.fading_stars = list(filter(lambda x: x[1] != drawing.C_BLACK, self.fading_stars))

        if len(self.fading_stars) <= self.max_fading_stars:
            if len(sample_space) > 0:
                rand_unprocessed_star = sample_space[random.randrange(len(sample_space))]
                # blow up that star:
                self.fading_stars.append((rand_unprocessed_star[0], drawing.C_WHITE + 1))

        # decrease the color of each fading star:
        self.fading_stars = [(x[0], x[1] - 1) for x in self.fading_stars]

        # apply fading stars to the matrix:
        for x in self.fading_stars:
            self.matrix[x[0]] = x

        draw = ImageDraw.Draw(img)
        # apply matrix on the image:
        for p in list(filter(lambda x: x[1] != self.NOT_PROCESSED_YET, self.matrix)):
            x = (p[0] % self.w) * self.star_size
            y = (p[0] // self.w) * self.star_size
            draw.rectangle(((x, y), (x + self.star_size, y + self.star_size)), p[1])

        return img


class Snake(Screensaver):
    def __init__(self, width: int, height: int, size=8):
        super().__init__(width, height)
        self.size = size
        self.w = math.ceil(width / self.size)
        self.h = math.ceil(height / self.size)
        self.position = -1

    def draw(self, img: Image) -> Image:
        draw = ImageDraw.Draw(img)

        if self.position > (self.w * self.h) + 16:
            draw.rectangle(((0, 0), (self.width - 1, self.height - 1)), drawing.C_BLACK)

        else:
            self.position += 1

            color = drawing.C_WHITE
            for p in reversed(range(0, self.position + 1)):
                p_x = p % self.w

                if p // self.w % 2 != 0:
                    p_x = self.w - p_x - 1

                x = p_x * self.size
                y = (p // self.w) * self.size
                draw.rectangle(((x, y), (x + self.size, y + self.size)), color)
                if color > drawing.C_BLACK:
                    color -= 1

        return img


if __name__ == "__main__":

    # image = Image.open("test.bmp")
    # image = Image.new('L', (1280, 960), drawing.C_BLACK + 6)
    x = 128
    y = 96
    # x = 100
    # y = 100
    ss = Snake(x, y, size=8)

    while True:
        # image = Image.open("test.bmp")
        image = Image.new('L', (x, y), drawing.C_BLACK + 6)
        image = ss.draw(image)
        image = image.point(lambda p: p * 16)
        # image.show()
        image.save("out.bmp")
        time.sleep(0.2)
