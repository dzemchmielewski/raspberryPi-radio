#!/usr/bin/python
import os.path
import platform

from entities import Station, SECOND

FULL_LOAD = True
if platform.uname().machine == "x86_64":
    FULL_LOAD = False

if FULL_LOAD:
    SPLASH_SCREEN_DISPLAY = 1 * 1_000
else:
    SPLASH_SCREEN_DISPLAY = 0 * 1_000

STATIONS = (
    Station("Radio Nowy Swiat", "RNS", "http://stream.rcs.revma.com/ypqt40u0x1zuv"),
    Station("TOK FM", "TOKFM", "http://poznan5-4.radio.pionier.net.pl:8000/tuba10-1.mp3"),
    #Station("Los 40 Classic", "LOS40CS", "https://20133.live.streamtheworld.com/LOS40_CLASSICAAC_SC"),
    Station("Los 40 Classic", "LOS40CS", "https://22333.live.streamtheworld.com/LOS40_CLASSICAAC.aac"),
    Station("RFI Monde", "RFIMON", "https://rfimonde64k.ice.infomaniak.ch/rfimonde-64.mp3"),
    Station("Radio 357", "R357", "https://stream.radio357.pl"),
    Station("Trójka", "PR3", "http://mp3.polskieradio.pl:8904/"),
    Station("Antyradio Classic Rock", "ANTCLA", "https://an04.cdn.eurozet.pl/ANTCLA.mp3"),
    Station("Złote przeboje", "ZP", "https://radiostream.pl/tuba9-1.mp3"),
    Station("Los 40", "LOS40", "https://25683.live.streamtheworld.com/LOS40.mp3"),
    Station("Classic America", "CLASM", "https://ice3.securenetsystems.net/CLASM"),

#    Station("Loca FM", "LOCFM", "http://s3.we4stream.com:8045/liv?2"),
#    Station("", "", ""),
)

SELECT_STATION_COMMIT_TIME = 1.7 * SECOND

RT_CURRENT_STATION = "rt/current_station"
CACHE_PERSISTENCE_DIR = "persist/"
if not os.path.isdir(CACHE_PERSISTENCE_DIR):
    os.mkdir(CACHE_PERSISTENCE_DIR)

RE2_LEFT_PIN = 20
RE2_RIGHT_PIN = 21
RE2_CLICK_PIN = 16

RE1_LEFT_PIN = 23
RE1_RIGHT_PIN = 24
RE1_CLICK_PIN = 18

LED_BLUE_PIN = 14
LED_GREEN_PIN = 19
LED_RED_PIN = 26

BTN2_PIN = 0
BTN3_PIN = 5
BTN4_PIN = 6
BTN5_PIN = 13


DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 96

with open("confidential/AudD-api-token.txt") as fp:
    AUDD_API_TOKEN = fp.readline().strip()
AUDD_URL = "https://api.audd.io/?api_token=" + AUDD_API_TOKEN
AUDD_CLIP_DIRECTORY = "clips/"
AUDD_CLIP_DURATION = 5 * 1_000

with open("confidential/visualcrossing.com-api-token.txt") as fp:
    VISUALCROSSING_TOKEN = fp.readline().strip()
VISUALCROSSING_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/Toru%C5%84"

VLC_HOST = "localhost"
VLC_PORT = 4444

MQTT_HOST = "192.168.0.21"
MQTT_PORT = 1883
from confidential.mqtt import MQTT_USERNAME, MQTT_PASSWORD
MQTT_TOPIC = "homectrl/device/radio/data"
MQTT_TOPIC_LIVE = "homectrl/device/radio/live"
