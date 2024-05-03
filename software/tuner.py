import json
import os
import re
import shlex
import socket
import subprocess
import urllib
from threading import Thread
from time import sleep

import requests

from bus import Bus
from configuration import AUDD_CLIP_DIRECTORY, AUDD_CLIP_DURATION, AUDD_URL, VLC_HOST, VLC_PORT
from entities import RadioItem, TUNER_OUTPUT_LOG, TunerStatus, RecognizeStatus, Station, RecognizeState, now


class Player:

    def __init__(self):
        self.host = VLC_HOST
        self.port = VLC_PORT
        # os.environ["VLC_VERBOSE"] = "3"
        self.pro = subprocess.Popen(shlex.split("/usr/bin/cvlc -I rc  --rc-host={}:{}".format(self.host, self.port)),
                                    stdout=subprocess.PIPE, shell=False, preexec_fn=os.setsid)
        self.debug = False
        if self.debug:
            print("[VLC INIT] {}".format(self.pro))
        self.vlc_client = None

    def _connect(self):
        self.vlc_client = socket.socket()
        successfully_connected = False
        attempts = 0

        while not successfully_connected and attempts < 5:
            try:
                self.vlc_client.connect((self.host, self.port))
                successfully_connected = True
            except ConnectionRefusedError:
                sleep(0.1)
                attempts += 1

        if not successfully_connected:
            raise ConnectionRefusedError("After {} attempts".format(attempts))

        # get welcome message from server, and ignore it:
        data = ""
        while not data.endswith("> "):
            data += self.vlc_client.recv(2048).decode()
        if self.debug:
            print("[VLC 1ST CALL] \"{}\"".format(data))

    def _vlc_cmd(self, cmd, read_response=True):
        if self.vlc_client is None:
            self._connect()

        self.vlc_client.send((cmd + "\n").encode())

        if read_response:
            data = ""
            while not data.endswith("> "):
                data += self.vlc_client.recv(2048).decode()

            if self.debug:
                print("[VLC RESPONSE] \"{}\"".format(data))

            return data

    def play(self, url):
        self._vlc_cmd("add {}".format(url))

    def info(self):
        info = self._vlc_cmd("info")
        f = re.findall(re.escape("now_playing: ") + "(.*)" + re.escape("\n"), info)
        if len(f) > 0 and len(f[0].strip()) > 0:
            if self.debug:
                print("[VLC INFO] \"{}\"".format(f[0].strip()))
            return f[0].strip()
        return None

    def is_playing(self):
        return self._vlc_cmd("is_playing")[0].strip() == "1"

    def exit(self):
        self._vlc_cmd("shutdown", read_response=False)
        self.vlc_client.close()
        # os.killpg(os.getpgid(self.pro.pid), signal.SIGTERM)


class Tuner(RadioItem):
    CODE = "tuner"
    EVENT_STATION = "station"
    EVENT_PLAY_STATUS = "status"
    EVENT_PLAY_INFO = "info"
    EVENT_RECOGNIZE = "recognize"
    EVENT_RECOGNIZE_STATUS = "recognize_status"

    def __init__(self):
        super(Tuner, self).__init__(Bus(TUNER_OUTPUT_LOG, Tuner.CODE))
        self.player = Player()
        self.is_playing = False
        self.current_station = None
        self.info = None
        self.recognizing_thread = None

    def exit(self):
        self.player.exit()

    def status(self):
        if self.is_playing:
            return TunerStatus.PLAYING
        return TunerStatus.TUNING

    def __recognize__(self, station: Station):
        self.bus.send_manager_event(Tuner.EVENT_RECOGNIZE_STATUS, RecognizeStatus(RecognizeState.CONNECTING, station))
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7"}
            request = urllib.request.Request(station.url, None, headers)
            stream = urllib.request.urlopen(request)
            # stream = urlopen(station.url)

            begin = now()
            file_path = AUDD_CLIP_DIRECTORY + station.code + "-" + str(begin) + ".mp3"
            fd = open(file_path, "wb")
            self.bus.send_manager_event(Tuner.EVENT_RECOGNIZE_STATUS, RecognizeStatus(RecognizeState.RECORDING, station))

            while now() - begin < AUDD_CLIP_DURATION:
                data = stream.read(10000)
                fd.write(data)
            fd.close()

            self.bus.send_manager_event(Tuner.EVENT_RECOGNIZE_STATUS, RecognizeStatus(RecognizeState.QUERYING, station))

            with open(file_path, "rb") as f:
                r = requests.post(AUDD_URL, files={'file': f})
                response = json.loads(r.text)

            result = RecognizeStatus(RecognizeState.DONE, station, response)
            self.bus.log("Recognize: {}[{}]".format(result, result.json))
            self.bus.send_manager_event(Tuner.EVENT_RECOGNIZE_STATUS, result)

        except requests.exceptions.RequestException as e:
            self.bus.log("Error querying AudD: " + str(e))
            self.bus.send_manager_event(Tuner.EVENT_RECOGNIZE_STATUS,
                                        RecognizeStatus(RecognizeState.DONE, station, json.loads("{\"status\":\"error\"}")))

        except urllib.error.HTTPError as e:
            self.bus.log("Error opening stream (" + station.url + "): " + str(e))
            self.bus.send_manager_event(Tuner.EVENT_RECOGNIZE_STATUS,
                                        RecognizeStatus(RecognizeState.DONE, station, json.loads("{\"status\":\"error\"}")))

    def loop(self):
        if (station := self.bus.consume_event(Tuner.EVENT_STATION)) is not None:
            if self.current_station != station or not self.is_playing:
                # First notify about the sound break:
                self.is_playing = False
                self.bus.send_manager_event(Tuner.EVENT_PLAY_STATUS, self.status())
                # Then change the station:
                # self.bus.log("Playing " + str(station))
                self.current_station = station
                self.player.play(station.url)
            else:
                # already playing that station...
                self.bus.send_manager_event(Tuner.EVENT_PLAY_STATUS, self.status())

        elif self.bus.consume_event(Tuner.EVENT_RECOGNIZE) is not None:
            if self.recognizing_thread is None or not self.recognizing_thread.is_alive():
                self.recognizing_thread = Thread(target=self.__recognize__, args=[self.current_station])
                self.recognizing_thread.start()

        else:
            current_playing_status = self.player.is_playing()
            if self.is_playing != current_playing_status:
                self.is_playing = current_playing_status
                self.bus.send_manager_event(Tuner.EVENT_PLAY_STATUS, self.status())

            if self.is_playing and (info := self.player.info()) != self.info:
                self.info = info
                if info is not None:
                    self.bus.send_manager_event(Tuner.EVENT_PLAY_INFO, self.info)
