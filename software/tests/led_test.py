from time import sleep

from gpiozero import LED

# led = LED(19)
led = LED(26)

try:
    while True:
        led.on()
        sleep(0.5)
        led.off()
        sleep(0.5)

        led.on()
        sleep(0.1)
        led.off()
        sleep(0.1)

except KeyboardInterrupt:
    exit()
