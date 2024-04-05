import sys
from time import sleep

sys.path.append('../')
from inputs import RotaryEncoder


def value_changed(direction):
    print("* New rotation - direction: {}".format(direction))


e1 = RotaryEncoder(20, 26, value_changed)

try:
    while True:
        sleep(5)
        print("Nothing...")
except Exception:
    pass
