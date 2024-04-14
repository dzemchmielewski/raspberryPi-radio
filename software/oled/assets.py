import os

from PIL import ImageFont


class Assets:

    assets_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'assets')

    font_path = os.path.join(assets_dir, 'Font.ttc')
    font_miscfixed_path = os.path.join(assets_dir, 'misc-fixed-bold-r-normal--15-140-75-75-c-90-i.ttf')
    font_dejavu_path = os.path.join(assets_dir, 'DejaVuSansMono.ttf')
    font_m3x6_path = os.path.join(assets_dir, 'm5x7.ttf')

    mordeczka = os.path.join(assets_dir, 'mordeczka.bmp')
    dzem_radio_sig = os.path.join(assets_dir, 'dzem-radio-sig.bmp')

    font_oled = ImageFont.truetype(font_path, 8)

    mainfont_0 = ImageFont.truetype(font_m3x6_path, 8)
    mainfont_1 = ImageFont.truetype(font_m3x6_path, 16)
    mainfont_2 = ImageFont.truetype(font_m3x6_path, 24)
    mainfont_3 = ImageFont.truetype(font_m3x6_path, 32)
    mainfont_4 = ImageFont.truetype(font_m3x6_path, 40)
    mainfont_5 = ImageFont.truetype(font_m3x6_path, 48)
    mainfont_6 = ImageFont.truetype(font_m3x6_path, 56)
    mainfont_7 = ImageFont.truetype(font_m3x6_path, 64)
    mainfont_8 = ImageFont.truetype(font_m3x6_path, 72)
    mainfont_9 = ImageFont.truetype(font_m3x6_path, 80)


