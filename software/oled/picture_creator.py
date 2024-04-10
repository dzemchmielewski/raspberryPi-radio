import sys
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
sys.path.append('.')

from oled.assets import Assets


class PictureCreator:

    WIDTH = 128
    HEIGHT = 96
    COLOR_SCALE = 16
    C_WHITE = 15
    C_BLACK = 0

    def __init__(self):
        self.temporary_volume_counter = 0
        self.volume_event = None

    @staticmethod
    def dim(draw, text, font):
        (x0, y0, x1, y1) = draw.textbbox((0, 0), text, font=font, anchor="lt")
        # print(text + " => " + str((x0, x1, y0, y1)))
        return x1 - x0, y1 - y0

    def frame(self, draw):
        draw.line([(0, 0), (127, 0)], fill=8)
        draw.line([(127, 0), (127, 95)], fill=8)
        draw.line([(127, 95), (0, 95)], fill=8)
        draw.line([(0, 95), (0, 0)], fill=8)

    def time(self, draw):
        font1 = ImageFont.truetype(Assets.font_path, 25)
        font2 = ImageFont.truetype(Assets.font_path, 10)
        now = datetime.now()

        text = [now.strftime("%p"), now.strftime("%I:%M"), now.strftime("%S")]

        dims = [self.dim(draw, text[0], font2), self.dim(draw, text[1], font1), self.dim(draw, text[2], font2)]

        x = round((self.WIDTH - sum(x for x, y in dims)) / 2)
        y = 30

        draw.text((x, y), text[0], font=font2, fill=self.C_WHITE - 6, anchor="lt")
        draw.text((x + dims[0][0], y), text[1], font=font1, fill=self.C_WHITE, anchor="lt")
        draw.text((x + sum(x for x, y in dims[0:2]), y), text[2], font=font2, fill=self.C_WHITE - 6, anchor="lt")

        y += max(y for x, y in dims) + 2

        date = now.strftime("%A, %-d %B %Y")
        x = round((self.WIDTH - self.dim(draw, date, font2)[0]) / 2)
        draw.text((x, y), date, font=font2, fill=self.C_WHITE - 4)

        y += self.dim(draw, date, font2)[1] + 2

        font3 = ImageFont.truetype(Assets.font1_path, 10)
        x = round((self.WIDTH - self.dim(draw, date, font3)[0]) / 2)
        draw.text((x, y), date, font=font3, fill=self.C_WHITE - 4)

    def text(self, draw, text, font_size, y):
        font = ImageFont.truetype(Assets.font_path, 35)

        length = round(font.getlength(text))
        # align middle:
        x = int((self.WIDTH - length) / 2)

        draw.text((x, y), text, font=font, fill=self.COLOR_SCALE - 1)

        bbox = draw.textbbox((x, y), text, font=font)
        print(bbox)

        self.frame(draw)

    def control_page(self, draw):
        for i in range(0, 16):
            draw.rectangle([(4 * i, 0), (4 * (i + 1), 96)], fill=i)
        for i in range(0, 16):
            draw.rectangle([(4 * i + 64, 0), (4 * (i + 1) + 64, 96)], fill=i)
        self.frame(draw)

    def volume_method_to_refactor(self, volume_event):
        self.volume_event = volume_event
        self.temporary_volume_counter = 0

    def main(self):
        image = Image.new('L', (self.WIDTH, self.HEIGHT), 0)
        draw = ImageDraw.Draw(image)
        # self.text(draw, "Test dzem", 18, 10)
        self.time(draw)
        self.frame(draw)

        if self.volume_event is not None and self.temporary_volume_counter <= 6:
            self.temporary_volume_counter += 1
            self.text(draw, str(self.volume_event.current_status.volume) + "%", 15, 60)

        return image


if __name__ == "__main__":
    creator = PictureCreator()
    image = creator.main()
    image = image.point(lambda p: p * 16)
    # image.show()
    image.save("out.bmp")
