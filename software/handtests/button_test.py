import sys
import time

sys.path.append('../')
from hardware import Button


def clicked():
    print("CLICKED!!!")


button = Button(12, clicked)
#PCB:
#button = Button(5, clicked)

try:
    while True:
        time.sleep(5)
        pass

except KeyboardInterrupt:
    exit()
