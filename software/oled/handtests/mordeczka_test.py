import sys
from time import sleep

from PIL import Image, ImageDraw

sys.path.append('../../')

from oled.lib import OLED_1in32
from assets import Assets

def control_page(draw):
    for i in range(0, 16):
        draw.rectangle([(4 * i, 0), (4 * (i + 1), 96)], fill=i)
    for i in range(0, 16):
        draw.rectangle([(4 * i + 64, 0), (4 * (i + 1) + 64, 96)], fill=i)


if __name__ == "__main__":

    try:
        disp = OLED_1in32.OLED_1in32()
        print("START!")
        disp.Init()
        print("CLEAR DISPLAY...")
        disp.clear()

        image = Image.new('L', (disp.width, disp.height), 0)  # 0: clear the frame
        bmp = Image.open(Assets.mordeczka)

        while True:
            image.paste(bmp, (0, 0))
            disp.ShowImage(disp.getbuffer(image))
            sleep(3)
            draw = ImageDraw.Draw(image)
            control_page(draw)
            disp.ShowImage(disp.getbuffer(image))
            sleep(3)

    except KeyboardInterrupt:
        disp.module_exit()
        exit()
