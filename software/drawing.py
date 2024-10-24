import random
from datetime import datetime
from functools import cache
from operator import itemgetter

from PIL import Image, ImageDraw, ImageFont, ImageEnhance

from assets import Assets
from entities import AstroData, time_f, MeteoData

COLOR_SCALE = 16
C_WHITE = 15
C_BLACK = 0


def display_month(m: int) -> str:
    match m:
        case 1:
            return "stycznia"
        case 2:
            return "lutego"
        case 3:
            return "marca"
        case 4:
            return "kwietnia"
        case 5:
            return "maja"
        case 6:
            return "czerwca"
        case 7:
            return "lipca"
        case 8:
            return "sierpnia"
        case 9:
            return "września"
        case 10:
            return "października"
        case 11:
            return "listopada"
        case 12:
            return "grudnia"
        case _:
            return "  --  "


def display_week_day(d: int) -> str:
    match d:
        case 6:
            return "niedziela"
        case 0:
            return "poniedziałek"
        case 1:
            return "wtorek"
        case 2:
            return "środa"
        case 3:
            return "czwartek"
        case 4:
            return "piątek"
        case 5:
            return "sobota"
        case _:
            return "  --  "


def dimension(draw, text, font):
    (x0, y0, x1, y1) = draw.textbbox((0, 0), text, font=font, anchor="lt")
    # print(text + " => " + str((x0, x1, y0, y1)))
    return x1 - x0, y1 - y0


def adjust_fonts(draw, width: int, text: [], fonts: [], horizontal_space: int, debug=False):
    dims = []
    for i in range(0, len(text)):
        dim = dimension(draw, text[i], fonts[i])
        while (dim[0] + horizontal_space) > width:
            fonts[i] = fonts[i].font_variant(size=fonts[i].size - 1)
            dim = dimension(draw, text[i], fonts[i])
        if debug:
            print("FS(" + str(i) + ") = " + str(fonts[i].size))
        dims += [dim]
    return dims, fonts


def frame(width, height):
    result = Image.new('L', (width, height), C_BLACK)
    draw = ImageDraw.Draw(result)
    __frame__(draw, (width, height))
    return result


def __frame__(draw, size, fill=None):
    width, height = size
    # draw.rectangle([(0, 0), (width - 1, height - 1)], outline=PictureCreator.C_WHITE)
    draw.rounded_rectangle([(0, 0), (width - 1, height - 1)], outline=C_WHITE, width=1, radius=3, fill=fill)


@cache
def top_bar(width, height=13, station="[]"):
    result = Image.new('L', (width, height), C_BLACK)
    draw = ImageDraw.Draw(result)
    # frame:
    __frame__(draw, (width, height), fill=C_BLACK + 5)
    # date:
    now = datetime.now()
    date = now.strftime("%a %d.%m.%Y")
    draw.text((3, 3), date, font=Assets.mainfont_1, fill=C_WHITE, anchor="lt")
    # station abbreviation:
    dim = dimension(draw, station, Assets.mainfont_1)
    draw.text((width - 3 - dim[0], 3), station, font=Assets.mainfont_1, fill=C_WHITE, anchor="lt")
    return result


@cache
def top_bar2(width, height, station=None):
    result = Image.new('L', (width, height), C_BLACK)
    draw = ImageDraw.Draw(result)
    # frame:
    __frame__(draw, (width, height), fill=C_BLACK + 5)
    # station:
    if station is not None:
        s = station.name
    else:
        s = " - "
    dim = dimension(draw, s, Assets.mainfont_1)
    draw.text((round((width - dim[0]) / 2), 3), s, font=Assets.mainfont_1, fill=C_WHITE, anchor="lt")
    return result


def bar(width: int, height: int = 13, text: str = ""):
    result = Image.new('L', (width, height), C_BLACK)
    draw = ImageDraw.Draw(result)
    # frame:
    __frame__(draw, (width, height), fill=C_BLACK + 5)
    draw.text((3, 3), text, font=Assets.mainfont_1, fill=C_WHITE, anchor="lt")
    return result


@cache
def splash_screen(width, height):
    result = Image.new('L', (width, height), C_BLACK)
    result.paste(Image.open(Assets.dzem_radio_sig), (7, 22))
    draw = ImageDraw.Draw(result)
    draw.rounded_rectangle([(1, 1), (width - 2, height - 2)], outline=C_WHITE - 3, width=3, radius=30)
    return result


def time(width):
    result = Image.new('L', (width, 0), C_BLACK)
    draw = ImageDraw.Draw(result)

    now = datetime.now()
    font = Assets.font_path
    text = [now.strftime("%p"), now.strftime("%I:%M"), now.strftime("%S")]
    fonts = [
        ImageFont.truetype(font, 14),
        ImageFont.truetype(font, 35),
        ImageFont.truetype(font, 14)]
    dims = [
        dimension(draw, text[0], fonts[0]),
        dimension(draw, text[1], fonts[1]),
        dimension(draw, text[2], fonts[2])]

    x = round((width - sum(x for x, y in dims)) / 2)
    max_y = max(dims, key=itemgetter(1))[1]

    result = result.resize((width, max_y))
    draw = ImageDraw.Draw(result)

    draw.text((x, 0), text[0], font=fonts[0], fill=C_WHITE - 6, anchor="lt")
    draw.text((x + dims[0][0], 0), text[1], font=fonts[1], fill=C_WHITE, anchor="lt")
    draw.text((x + sum(x for x, y in dims[0:2]), max_y - dims[2][1]), text[2], font=fonts[2], fill=C_WHITE - 6,
              anchor="lt")
    return result


@cache
def text_window(width, text=[], suggested_font_size=[], vertical_space=6, horizontal_space=6, is_frame=True, fill=C_BLACK + 3,
                font_path=Assets.font_path, fixed_width=False, debug=False) -> Image:
    if debug:
        print("width = {}".format(width))
    result = Image.new('L', (width, 0), C_BLACK)
    draw = ImageDraw.Draw(result)

    fonts = []
    for x in suggested_font_size:
        fonts += [ImageFont.truetype(font_path, x)]

    dims, fonts = adjust_fonts(draw, width, text, fonts, horizontal_space, debug=debug)

    if fixed_width:
        new_width = width
    else:
        new_width = max(dims, key=itemgetter(0))[0] + horizontal_space
    new_height = sum(y for x, y in dims[0:len(dims)]) + ((len(dims) + 1) * vertical_space)

    result = result.resize((new_width, new_height))
    draw = ImageDraw.Draw(result)

    if is_frame:
        draw.rounded_rectangle([(0, 0), (new_width - 1, new_height - 1)], outline=C_WHITE, width=1, radius=3, fill=fill)

    for i in range(0, len(text)):
        draw.text((round((new_width - dims[i][0]) / 2), vertical_space * (i + 1) + sum(y for x, y in dims[0:i])), text[i],
                  font=fonts[i], fill=C_WHITE, anchor="lt")

    return result


@cache
def select_station(width, text=[], vertical_space=6, horizontal_space=4, font_path=Assets.font_path) -> Image:
    result = Image.new('L', (width, 0), C_BLACK)
    draw = ImageDraw.Draw(result)

    fonts = [ImageFont.truetype(font_path, 12)] * len(text)
    dims, fonts = adjust_fonts(draw, width, text, fonts, horizontal_space, debug=False)

    new_height = sum(y for x, y in dims[0:len(dims)]) + ((len(dims) + 1) * vertical_space)

    result = result.resize((width, new_height))
    draw = ImageDraw.Draw(result)

    draw.rounded_rectangle([(0, 0), (width - 1, new_height - 1)], outline=C_WHITE - 5, width=4, radius=3, fill=C_WHITE)

    for i in range(0, len(text)):
        if len(text) // 2 == i:
            rec_from = (0 + 2, vertical_space * (i + 1) + sum(y for x, y in dims[0:i]) - (vertical_space // 2))
            rec_to = (width - 1 - 2, vertical_space * (i + 1 + 1) + sum(y for x, y in dims[0:i + 1]) - (vertical_space // 2))
            draw.rounded_rectangle((rec_from, rec_to), radius=5, fill=C_BLACK + 5)
            draw.text((round((width - dims[i][0]) / 2), vertical_space * (i + 1) + sum(y for x, y in dims[0:i])), text[i],
                      font=fonts[i], fill=C_WHITE, anchor="lt")
        else:
            draw.text((round((width - dims[i][0]) / 2), vertical_space * (i + 1) + sum(y for x, y in dims[0:i])), text[i],
                      font=fonts[i], fill=C_BLACK, anchor="lt")

    return result


@cache
def create_astro_strip(width: int, height: int, astro_data: AstroData) -> Image:
    result = Image.new('L', (width * 6, height), C_BLACK)

    # next_day = chr(8594)
    # prev_day = chr(8592)

    # Sun & Moon rise & set:
    icons = [Assets.sunrise, Assets.sunset, Assets.moonrise, Assets.moonset]
    if astro_data is None:
        text = [time_f(None)] * 4
    else:
        text = [time_f(astro_data.sunrise), time_f(astro_data.sunset), time_f(astro_data.moonrise), time_f(astro_data.moonset)]

    for i in range(0, len(icons)):
        img = Image.open(icons[i]).convert('L')
        img = ImageEnhance.Brightness(img).enhance(0.04)
        result.paste(img, (i * img.size[0], 0))
        time_img = text_window(width, tuple([text[i]]), tuple([20]), vertical_space=5, horizontal_space=0, is_frame=False,
                               font_path=Assets.font_path)
        result.paste(time_img, ((i * width) + round((width - time_img.size[0]) / 2), img.size[1] + 1))

    # Moon phase:
    phase_img = moon_phase(width, height, astro_data.moon_phase if astro_data is not None else None)
    result.paste(phase_img, ((4 * width) + round((width - phase_img.size[0]) / 2), 0))

    # Repeat first frame at the end:
    first_frame = result.crop([0, 0, width, height])
    result.paste(first_frame, (5 * width, 0))

    return result


@cache
def create_meteo_strip(width: int, height: int, meteo_data: MeteoData) -> Image:
    result = Image.new('L', (width * 4, height), C_BLACK)
    if meteo_data is None:
        return result

    i = 0
    img = Image.open(Assets.weather_icons + meteo_data.icon + ".png").convert('L')
    img.thumbnail((width, height), Image.Resampling.LANCZOS)
    result.paste(img, ((i * width) + round((width - img.size[0]) / 2), 0))

    i += 1
    degree = chr(176)
    text = [("{}" + degree + "C").format(meteo_data.temperature), "{}hPa".format(round(meteo_data.pressure))]
    img = text_window(width, tuple(text), tuple([20, 20]), vertical_space=4, horizontal_space=0,
                      is_frame=False,
                      font_path=Assets.font_path)
    result.paste(img, ((i * width) + round((width - img.size[0]) / 2), round((height - img.size[1]) / 2)))

    # km = chr(13214)
    # up_left_arrow = chr(8632)

    i += 1
    text = [("{} ({})").format(meteo_data.windspeed, meteo_data.windgust),
            "  km/h  ",
            ("{} {}" + degree).format(meteo_data.winddir_compass(), round(meteo_data.winddir))]
    img = text_window(width, tuple(text), tuple([15] * len(text)), vertical_space=1, horizontal_space=0,
                      is_frame=False,
                      font_path=Assets.font_path)
    result.paste(img, ((i * width) + round((width - img.size[0]) / 2), round((height - img.size[1]) / 2)))

    # Repeat first frame at the end:
    i += 1
    first_frame = result.crop([0, 0, width, height])
    result.paste(first_frame, (i * width, 0))

    return result


@cache
def create_date_strip(width: int, height: int, text, description, horizontally=False):
    frames = 1
    if description is not None:
        frames = 3
        if isinstance(split(description)[0], list):
            frames += 1

    if horizontally:
        result = Image.new('L', (frames * width, height), C_BLACK)

        def x_frame_offset(i: int):
            return i * width

        def y_frame_offset(i: int):
            return 0

    else:
        result = Image.new('L', (width, frames * height), C_BLACK)

        def x_frame_offset(i: int):
            return 0

        def y_frame_offset(i: int):
            return i * height

    img = text_window(width, tuple(text), tuple([20] * len(text)), is_frame=False, vertical_space=2,
                      fill=C_BLACK)
    i = 0
    result.paste(img, (x_frame_offset(i) + round((width - img.size[0]) / 2), y_frame_offset(i) + round((height - img.size[1]) / 2)))

    if description is not None:
        desc = split(description)
        if isinstance(desc[0], list):
            for d in desc:
                i += 1
                img = text_window(width, tuple(d), tuple([13] * len(d)), is_frame=False, vertical_space=2,
                                  fill=C_BLACK)
                result.paste(img,
                             (x_frame_offset(i) + round((width - img.size[0]) / 2), y_frame_offset(i) + round((height - img.size[1]) / 2)))
        else:
            i += 1
            img = text_window(width, tuple(desc), tuple([13] * len(desc)), is_frame=False, vertical_space=2,
                              fill=C_BLACK)
            result.paste(img, (x_frame_offset(i) + round((width - img.size[0]) / 2), y_frame_offset(i) + round((height - img.size[1]) / 2)))

        # Repeat first frame at the end:
        i += 1
        first_frame = result.crop([0, 0, width, height])
        result.paste(first_frame, (x_frame_offset(i), y_frame_offset(i)))

    return result


@cache
def create_time_strip(width: int, height: int, text, holidays: [str], horizontally=False):
    frames = 1
    if holidays is not None and len(holidays) > 0:
        frames = 3

    if horizontally:
        result = Image.new('L', (frames * width, height), C_BLACK)

        def x_frame_offset(i: int):
            return i * width

        def y_frame_offset(i: int):
            return 0

    else:
        result = Image.new('L', (width, frames * height), C_BLACK)

        def x_frame_offset(i: int):
            return 0

        def y_frame_offset(i: int):
            return i * height

    img = text_window(width, tuple(text), tuple([34]), is_frame=False, fill=C_BLACK, debug=False)

    i = 0
    result.paste(img, (x_frame_offset(i) + round((width - img.size[0]) / 2), y_frame_offset(i) + round((height - img.size[1]) / 2)))

    if holidays is not None and len(holidays) > 0:
        desc = split(holidays[random.randint(0, len(holidays) - 1)], 13, True)

        i += 1
        img = text_window(width, tuple(desc), tuple([13] * len(desc)), is_frame=False, vertical_space=2, fill=C_BLACK)
        result.paste(img, (x_frame_offset(i) + round((width - img.size[0]) / 2), y_frame_offset(i) + round((height - img.size[1]) / 2)))

        # Repeat first frame at the end:
        i += 1
        first_frame = result.crop([0, 0, width, height])
        result.paste(first_frame, (x_frame_offset(i), y_frame_offset(i)))

    return result


def __volume__(width: int, height: int, volume: int, fill):
    result = Image.new('L', (width, height), fill)
    draw = ImageDraw.Draw(result)

    draw.polygon([(0, height - 1), (width - 1, height - 1), (width - 1, 0)], outline=C_WHITE - 5, fill=C_BLACK + 6)
    x = round((width * volume) / 100)
    y = round((height * (100 - volume)) / 100)
    draw.polygon([(0, height - 1), (x - 1, height - 1), (x - 1, y)], fill=C_WHITE)

    return result


@cache
def volume_window(width: int, height: int, volume: int, fill=C_BLACK, margin=3, mute=False):
    result = Image.new('L', (width, height), C_BLACK)
    draw = ImageDraw.Draw(result)

    draw.rounded_rectangle([(0, 0), (width - 1, height - 1)], outline=C_WHITE, width=1, radius=3, fill=fill)
    if mute:
        img = Image.open(Assets.mute)
    else:
        img = Image.open(Assets.speaker)  # .convert('L')
    result.paste(__volume__(width - 2 * margin, height - 2 * margin, volume, fill), (margin, margin))
    result.paste(img, (2, 2))
    return result


@cache
def _moon_phase(width: int, height: int, phase: float):
    result = Image.new('L', (width, height), C_BLACK)
    draw = ImageDraw.Draw(result)
    radius = round((min(width, height) - 2) / 2)
    x = round(width / 2)
    y = round(height / 2)

    # draw full moon:
    draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=C_WHITE - 6)

    # phase:
    # 0 - new moon, 0.25 - 1st qrt, 0.5 - full moon,  0.75 - 2nd qrt, 1 (or 0) - new moon
    # we have to scale phase to -2.0 ... 2.0, where:
    # -2.0  - full moon, -1.0 - 1st qrt, 0 - new moon, 1.0 - 2nd qrt, 2.0 (or -2.0) - full moon
    a = -((((phase + 0.5) % 1) * 4) - 2)
    # and that way find the middle of the earth shadow circle:
    x = x + a * radius

    # make a radius a little bit smaller, when around the full moon, so the new moon is somehow visible:
    # m_max - percentage of maximum radius difference
    # let's say it is 5%
    m_max = 5

    # margin - percentage of radius difference, depending on moon phase:
    # - for the full moon the margin is zero,
    # - margin raises up to m_max until the new moon
    # - then margin decreases to 0 until the full moon again
    margin = m_max - (m_max - round(((abs((phase * 2) - 1)) * m_max)))

    # calculate the radius of the earth shadow:
    radius = radius - (radius * (margin / 100))

    # and finally draw earth shadow:
    draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=C_BLACK)

    return result


@cache
def moon_phase(width: int, height: int, phase: float):
    result = Image.new('L', (width, height), C_BLACK)
    if phase is None:
        return result

    moon_phase_height = round(height - ((4 / 10) * height))
    if phase is not None:
        result.paste(_moon_phase(width, moon_phase_height, phase), (0, 0))

    text = str(round(100 * (1 - (2 * abs(phase - 0.5)))))
    moon_text_img = text_window(width, tuple([text + "%"]), tuple([14]), vertical_space=2, horizontal_space=0, is_frame=False,
                                font_path=Assets.font_path)

    result.paste(moon_text_img, (
        round((width - moon_text_img.size[0]) / 2),
        moon_phase_height + round((height - moon_phase_height - moon_text_img.size[1]) / 2)))

    return result


@cache
def split(text: str, line_stops_after=11, one_frame_only=False) -> []:
    words = text.split()
    result = []

    for word in words:
        if len(result[-1:]) == 0 or len(result[-1]) > line_stops_after:
            result.append(word)
        else:
            result[-1] = "{} {}".format(result[-1], word)

    if (l := len(result)) > 3 and not one_frame_only:
        return [result[0:(l // 2)], result[l // 2:]]
    else:
        return result


if __name__ == "__main__":
    print(split("Cooling down with a chance of rain Friday."))
    print(split("Cooling down with a chance of rain Sunday & Monday."))

    values = [0, 15, 20, 45, 180, 190, 225, 300, 350]
    compass_sectors = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW", "N"]
    for v in values:
        print("{} -> {}".format(v, compass_sectors[round(v / 22.5)]))
