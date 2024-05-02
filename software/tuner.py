import json
import urllib
from threading import Thread

import requests
import vlc

from bus import Bus
from configuration import AUDD_CLIP_DIRECTORY, AUDD_CLIP_DURATION, AUDD_URL
from entities import RadioItem, TUNER_OUTPUT_LOG, TunerStatus, RecognizeStatus, Station, RecognizeState, now


class Tuner(RadioItem):
    CODE = "tuner"
    EVENT_STATION = "station"
    EVENT_PLAY_STATUS = "status"
    EVENT_RECOGNIZE = "recognize"
    EVENT_RECOGNIZE_STATUS = "recognize_status"

    def __init__(self):
        super(Tuner, self).__init__(Bus(TUNER_OUTPUT_LOG, Tuner.CODE))
        # TODO: read
        # echo $VLC_VERBOSE  3
        self.player = vlc.MediaPlayer()
        self.is_playing = False
        self.current_station = None
        self.recognizing_thread = None

    def exit(self):
        self.player.stop()

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

            file_path = AUDD_CLIP_DIRECTORY + station.code + "-" + str(begin) + ".mp3"
            fd = open(file_path, "wb")
            self.bus.send_manager_event(Tuner.EVENT_RECOGNIZE_STATUS, RecognizeStatus(RecognizeState.RECORDING, station))

            begin = now()
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
                self.player.set_media(vlc.Media(station.url))
                self.player.play()
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

