import sys
from time import sleep

sys.path.append('../')
from hardware import RotaryEncoder


def value_changed(direction):
    print("* New rotation - direction: {}".format(direction))


e1 = RotaryEncoder(23, 24, value_changed)
e2 = RotaryEncoder(20, 21, value_changed)

try:
    while True:
        sleep(5)
        print("Nothing...")
except Exception:
    pass
