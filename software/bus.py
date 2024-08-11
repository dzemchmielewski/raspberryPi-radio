#!/usr/bin/python
import os.path
import sys
from datetime import datetime

import dill
import pylibmc

from configuration import CACHE_PERSISTENCE_DIR
from entities import RADIO_MANAGER_CODE


class Bus:

    def __init__(self, logname, code):
        self.code = code
        self.logname = logname
        self.mc = pylibmc.Client(["127.0.0.1"], binary=True,
                                 behaviors={"tcp_nodelay": True,
                                            "ketama": True})
        self.pool = pylibmc.ThreadMappedPool(self.mc)
        self.debug = True
        self.persist = {}
        if os.path.isfile(CACHE_PERSISTENCE_DIR + self.code):
            with open(CACHE_PERSISTENCE_DIR + self.code, 'rb') as f:
                self.persist = dill.load(f)
            self.log("Loaded keys (" + self.code + "):" + str(self.persist))

    def __del__(self):
        self.pool.relinquish()

    def exit(self):
        if len(self.persist) > 0:
            with open(CACHE_PERSISTENCE_DIR + self.code, 'wb') as f:
                dill.dump(self.persist, f)
            self.log("Persisted keys (" + self.code + "):" + str(self.persist))

    def log(self, msg, now=None):
        if now is None:
            now = datetime.now()
        print("[" + "{:%Y-%m-%d %H:%M:%S.%f}".format(now) + "][" + self.logname + "] " + msg)
        sys.stdout.flush()

    def get(self, name):
        return self.persist.get(name, None)

    def set(self, name, value):
        self.persist[name] = value

    def consume_event(self, name):
        event_key = self.code + "/event/" + name
        with self.pool.reserve() as mc:
            event = mc.get(event_key)
            if event is not None:
                mc.delete(event_key)
                if self.debug:
                    self.log("Event consumed [" + event_key + " -> " + self.code + "]: " + str(event))
        return event

    def send_event(self, consumer_code, name, event):
        event_key = consumer_code + "/event/" + name
        with self.pool.reserve() as mc:
            if (prev_object := mc.get(event_key)) is None or prev_object != event:
                if self.debug:
                    self.log("Event sent     [" + self.code + " -> " + event_key + "]: " + str(event))
                return mc.set(event_key, event)

    def send_manager_event(self, name, event):
        self.send_event(RADIO_MANAGER_CODE, name, event)

    def set_value(self, name, value):
        with self.pool.reserve() as mc:
            return mc.set(name, value)

    def get_value(self, name):
        with self.pool.reserve() as mc:
            return mc.get(name)
