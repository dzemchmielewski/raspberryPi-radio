import os

from PIL import ImageFont


class Assets:

    assets_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'assets')

    font_path = os.path.join(assets_dir, 'Font.ttc')
    font_m5x7_path = os.path.join(assets_dir, 'm5x7.ttf')

    mordeczka = os.path.join(assets_dir, 'mordeczka.bmp')
    dzem_radio_sig = os.path.join(assets_dir, 'dzem-radio-sig.bmp')

    sunrise = os.path.join(assets_dir, 'sunmoon/sunrise-start.png_converted')
    sunset = os.path.join(assets_dir, 'sunmoon/sunset-start.png_converted')
    moonrise = os.path.join(assets_dir, 'sunmoon/moonrise-start.png_converted')
    moonset = os.path.join(assets_dir, 'sunmoon/moonset-start.png_converted')

    speaker = os.path.join(assets_dir, 'speaker/speaker.bmp_converted')
    mute = os.path.join(assets_dir, 'speaker/mute.bmp_converted')

    font_oled = ImageFont.truetype(font_path, 8)

    mainfont_0 = ImageFont.truetype(font_m5x7_path, 8)
    mainfont_1 = ImageFont.truetype(font_m5x7_path, 16)
    mainfont_2 = ImageFont.truetype(font_m5x7_path, 24)
    mainfont_3 = ImageFont.truetype(font_m5x7_path, 32)
    mainfont_4 = ImageFont.truetype(font_m5x7_path, 40)
    mainfont_5 = ImageFont.truetype(font_m5x7_path, 48)
    mainfont_6 = ImageFont.truetype(font_m5x7_path, 56)
    mainfont_7 = ImageFont.truetype(font_m5x7_path, 64)
    mainfont_8 = ImageFont.truetype(font_m5x7_path, 72)
    mainfont_9 = ImageFont.truetype(font_m5x7_path, 80)

    weather_icons = os.path.join(assets_dir, 'WeatherIcons/4/')

