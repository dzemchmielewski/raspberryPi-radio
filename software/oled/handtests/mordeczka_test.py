import sys
from PIL import Image

sys.path.append('../../')

from oled.lib import OLED_1in32
from oled.assets import Assets

if __name__ == "__main__":

    try:
        disp = OLED_1in32.OLED_1in32()
        print("START!")
        disp.Init()
        print("CLEAR DISPLAY...")
        disp.clear()

        image = Image.new('L', (disp.width, disp.height), 0)  # 0: clear the frame
        bmp = Image.open(Assets.mordeczka)
        image.paste(bmp, (0, 0))
        disp.ShowImage(disp.getbuffer(image))

        while True:
            pass

    except KeyboardInterrupt:
        disp.module_exit()
        exit()
