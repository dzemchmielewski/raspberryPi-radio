#!/usr/bin/python
from entities import Station

STATIONS = (
    Station("Radio Nowy Świat", "RNS", "http://stream.rcs.revma.com/ypqt40u0x1zuv"),
    Station("TOK FM", "TOKFM", "http://poznan5-4.radio.pionier.net.pl:8000/tuba10-1.mp3"),
    Station("Los 40", "LOS40", "https://25683.live.streamtheworld.com/LOS40.mp3"),
    Station("Radio 357", "R357", "https://stream.radio357.pl"),
    Station("Trójka", "PR3", "http://mp3.polskieradio.pl:8904/"),
)

RT_CURRENT_STATION = "rt/current_station"

VOLUME_PIN_LEFT = 20
VOLUME_PIN_RIGHT = 26
VOLUME_PIN_CLICK = 21

LED_TUNER_STATUS = 16

# not connected yet
STATION_PIN_LEFT = 18
STATION_PIN_RIGHT = 19



#PCB connections:
#RE1:
#VOLUME_PIN_CLICK = 16 #phys 36
#VOLUME_PIN_LEFT = 20  #phys 38
#VOLUME_PIN_RIGHT = 21 #phys 40

#LED_TUNER_STATUS = 22
