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
    def text_window(width, text = [], suggested_font_size=[]) -> Image:
        result = Image.new('L', (width, 0), PictureCreator.C_BLACK)
        draw = ImageDraw.Draw(result)

        font = Assets.font_path
        fonts = []
        for x in suggested_font_size:
            fonts += [ImageFont.truetype(font, x)]

        dims = []
        for i in range(0, len(text)):
            dim = PictureCreator.dim(draw, text[i], fonts[i])
            while (dim[0]+6) > width:
                fonts[i] = fonts[i].font_variant(size=fonts[i].size - 1)
                dim = PictureCreator.dim(draw, text[i], fonts[i])
            dims += [dim]

        vertical_space = 6

        new_width = max(dims, key=itemgetter(0))[0] + 6
        new_height = sum(y for x, y in dims[0:len(dims)]) + ((len(dims)+1)*vertical_space)

        result = result.resize((new_width, new_height))
        draw = ImageDraw.Draw(result)

        PictureCreator.__frame__(draw, new_width, new_height, fill=PictureCreator.C_BLACK + 3)

        for i in range(0, len(text)):
            draw.text((round((new_width - dims[i][0]) / 2), vertical_space*(i+1) + sum(y for x,y in dims[0:i])), text[i], font=fonts[i], fill=PictureCreator.C_WHITE, anchor="lt")

        return result
