import math
import random
import time

from PIL import ImageDraw, Image

import drawing


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

    def draw(self, img: Image) -> Image:

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


if __name__ == "__main__":

    # image = Image.open("test.bmp")
    image = Image.new('L', (1280, 960), drawing.C_BLACK + 6)
    ss = FadingStars(image.size[0], image.size[1], star_size=100)

    while True:
        # image = Image.open("test.bmp")
        image = Image.new('L', (1280, 960), drawing.C_BLACK + 6)
        image = ss.draw(image)
        image = image.point(lambda p: p * 16)
        # image.show()
        image.save("out.bmp")
        time.sleep(0.1)
