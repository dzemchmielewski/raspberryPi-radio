import sys
from time import sleep

sys.path.append('../')
from inputs import RotaryButton


def clicked():
    print("CLICKED!!!")


button = RotaryButton(18, clicked)

try:
    while True:
        sleep(5)
        pass

except KeyboardInterrupt:
    exit()
