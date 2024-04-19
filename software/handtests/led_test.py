from signal import pause
from time import sleep

from gpiozero import LED, PWMLED

#led = LED(12)
led = PWMLED(12)

def test1():
    while True:
        led.on()
        sleep(0.5)
        led.off()
        sleep(0.5)

        led.on()
        sleep(0.1)
        led.off()
        sleep(0.1)

def test2():
    while True:
        for  i in range(0, 10):
            print("VAL = " + str(i*0.1))
            led.value = i * 0.1

            sleep(0.5)

try:
    test2()
    led.value = 0.1
    pause()


except KeyboardInterrupt:
    exit()
