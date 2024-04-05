import sys
from time import sleep

sys.path.append('../../')

from oled.picture_creator import PictureCreator
from oled.lib import OLED_1in32

if __name__ == "__main__":

    try:
        disp = OLED_1in32.OLED_1in32()
        print("START!")
        disp.Init()
        print("CLEAR DISPLAY...")
        disp.clear()

        creator = PictureCreator()

        while True:
            image = creator.main()
            disp.ShowImage(disp.getbuffer(image))
            sleep(0.2)

    except KeyboardInterrupt:
        disp.module_exit()
        exit()
