#!/usr/bin/python
import platform

from entities import Station

FULL_LOAD = True
if platform.uname().machine == "x86_64":
    FULL_LOAD = False

if FULL_LOAD:
    SPLASH_SCREEN_DISPLAY = 4 * 1_000
else:
    SPLASH_SCREEN_DISPLAY = 0 * 1_000

STATIONS = (
    Station("Radio Nowy Swiat", "RNS", "http://stream.rcs.revma.com/ypqt40u0x1zuv"),
    Station("TOK FM", "TOKFM", "http://poznan5-4.radio.pionier.net.pl:8000/tuba10-1.mp3"),
    Station("Los 40", "LOS40", "https://25683.live.streamtheworld.com/LOS40.mp3"),
    Station("Radio 357", "R357", "https://stream.radio357.pl"),
    Station("Trójka", "PR3", "http://mp3.polskieradio.pl:8904/"),
)

RT_CURRENT_STATION = "rt/current_station"

RE2_LEFT_PIN = 20
RE2_RIGHT_PIN = 21
RE2_CLICK_PIN = 16

RE1_LEFT_PIN = 23
RE1_RIGHT_PIN = 24
RE1_CLICK_PIN = 18

LED_BLUE_PIN = 14
LED_RED_PIN = 19
LED_GREEN_PIN = 26

BTN2_PIN = 0
BTN3_PIN = 5
BTN4_PIN = 6
BTN5_PIN = 13


DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 96

with open("external/AudD-api-token.txt") as fp:
    AUDD_API_TOKEN = fp.readline().strip()
AUDD_URL = "https://api.audd.io/?api_token=" + AUDD_API_TOKEN
AUDD_CLIP_DIRECTORY = "clips/"
AUDD_CLIP_DURATION = 5 * 1_000


with open("external/accuweather-api-token.txt") as fp:
    ACCUWEATHER_TOKEN = fp.readline().strip()
ACCUWEATHER_LOCATION_ID = "273877"
ACCUWEATHER_FORECAST_URL="http://dataservice.accuweather.com/forecasts/v1/daily/1day/" + ACCUWEATHER_LOCATION_ID + "?apikey=" + ACCUWEATHER_TOKEN + "&details=true&metric=true"
ACCUWEATHER_CURRENT_URL = "http://dataservice.accuweather.com/currentconditions/v1/" + ACCUWEATHER_LOCATION_ID + "?apikey=" + ACCUWEATHER_TOKEN + "&details=true"


with open("external/visualcrossing.com-api-token.txt") as fp:
    VISUALCROSSING_TOKEN = fp.readline().strip()
VISUALCROSSING_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/Toru%C5%84"
