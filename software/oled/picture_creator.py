import sys
from datetime import datetime
from operator import itemgetter

from PIL import Image, ImageDraw, ImageFont

sys.path.append('.')

from oled.assets import Assets


class PictureCreator:
    COLOR_SCALE = 16
    C_WHITE = 15
    C_BLACK = 0

    @staticmethod
    def dim(draw, text, font):
        (x0, y0, x1, y1) = draw.textbbox((0, 0), text, font=font, anchor="lt")
        # print(text + " => " + str((x0, x1, y0, y1)))
        return x1 - x0, y1 - y0

    @staticmethod
    def frame(width, height):
        result = Image.new('L', (width, height), PictureCreator.C_BLACK)
        draw = ImageDraw.Draw(result)
        PictureCreator.__frame__(draw, width, height)
        return result

    @staticmethod
    def __frame__(draw, width, height, fill=None):
        # draw.rectangle([(0, 0), (width - 1, height - 1)], outline=PictureCreator.C_WHITE)
        draw.rounded_rectangle([(0, 0), (width - 1, height - 1)], outline=PictureCreator.C_WHITE, width=1, radius=3, fill=fill)

    @staticmethod
    def top_bar(width, height=13, station="[]"):
        result = Image.new('L', (width, height), PictureCreator.C_BLACK)
        draw = ImageDraw.Draw(result)
        # frame:
        PictureCreator.__frame__(draw, width, height, fill=PictureCreator.C_BLACK + 5)
        # date:
        now = datetime.now()
        date = now.strftime("%a %d.%m.%Y")
        draw.text((3, 3), date, font=Assets.mainfont_1, fill=PictureCreator.C_WHITE, anchor="lt")
        # station abbreviation:
        dim = PictureCreator.dim(draw, station, Assets.mainfont_1)
        draw.text((width - 3 - dim[0], 3), station, font=Assets.mainfont_1, fill=PictureCreator.C_WHITE, anchor="lt")
        return result

    @staticmethod
    def time(width):
        result = Image.new('L', (width, 0), PictureCreator.C_BLACK)
        draw = ImageDraw.Draw(result)

        now = datetime.now()
        font = Assets.font_path
        text = [now.strftime("%p"), now.strftime("%I:%M"), now.strftime("%S")]
        fonts = [
            ImageFont.truetype(font, 14),
            ImageFont.truetype(font, 35),
            ImageFont.truetype(font, 14)]
        dims = [
            PictureCreator.dim(draw, text[0], fonts[0]),
            PictureCreator.dim(draw, text[1], fonts[1]),
            PictureCreator.dim(draw, text[2], fonts[2])]

        x = round((width - sum(x for x, y in dims)) / 2)
        max_y = max(dims, key=itemgetter(1))[1]

        result = result.resize((width, max_y))
        draw = ImageDraw.Draw(result)

        draw.text((x, 0), text[0], font=fonts[0], fill=PictureCreator.C_WHITE - 6, anchor="lt")
        draw.text((x + dims[0][0], 0), text[1], font=fonts[1], fill=PictureCreator.C_WHITE, anchor="lt")
        draw.text((x + sum(x for x, y in dims[0:2]), max_y - dims[2][1]), text[2], font=fonts[2], fill=PictureCreator.C_WHITE - 6, anchor="lt")
        return result

    @staticmethod
    def tuner_status(width, text = []):
        result = Image.new('L', (width, 0), PictureCreator.C_BLACK)
        draw = ImageDraw.Draw(result)

        font = Assets.font_path
        fonts = [
            ImageFont.truetype(font, 12),
            ImageFont.truetype(font, 18)]
        dims = [
            PictureCreator.dim(draw, text[0], fonts[0]),
            PictureCreator.dim(draw, text[1], fonts[1])]

        #TODO: fit text size to frame
        # fonts[0].font_variant()

        result = result.resize((width, dims[0][1] + dims[1][1] + 10))
        draw = ImageDraw.Draw(result)

        PictureCreator.__frame__(draw, width, dims[0][1] + dims[1][1] + 10, fill=PictureCreator.C_BLACK + 3)

        draw.text((round((width - dims[0][0]) / 2), 4), text[0], font=fonts[0], fill=PictureCreator.C_WHITE, anchor="lt")
        draw.text((round((width - dims[1][0]) / 2), dims[0][1]  + 2 + 4), text[1], font=fonts[1], fill=PictureCreator.C_WHITE, anchor="lt")

        return result



class PictureCreatorDEPRECTATED:
    WIDTH = 128
    HEIGHT = 96
    COLOR_SCALE = 16
    C_WHITE = 15
    C_BLACK = 0

    def __init__(self):
        self.temporary_volume_counter = 0
        self.volume_event = None

    def time(self, draw):
        font1 = ImageFont.truetype(Assets.font_path, 25)
        font2 = ImageFont.truetype(Assets.font_path, 10)
        now = datetime.now()

        text = [now.strftime("%p"), now.strftime("%I:%M"), now.strftime("%S")]
        fonts = []

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

        font3 = ImageFont.truetype(Assets.font_miscfixed_path, 10)
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
