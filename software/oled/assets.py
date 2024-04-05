import os


class Assets:

    assets_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'assets')
    font_path = os.path.join(assets_dir, 'Font.ttc')
    font1_path = os.path.join(assets_dir, 'misc-fixed-bold-r-normal--15-140-75-75-c-90-i.ttf')

    mordeczka = os.path.join(assets_dir, 'mordeczka.bmp')
