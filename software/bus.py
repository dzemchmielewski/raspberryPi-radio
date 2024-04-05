#!/usr/bin/python

from datetime import datetime
import pylibmc

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

    def __del__(self):
        self.pool.relinquish()

    def log(self, msg, now=None):
        if now is None:
            now = datetime.now()
        print("[" + "{:%Y-%m-%d %H:%M:%S.%f}".format(now) + "][" + self.logname + "] " + msg)

    def get(self, name):
        with self.pool.reserve() as mc:
            return mc.get(self.code + "/" + name)

    # def getBool(self, name):
    #     value = self.mc.get(self.code + "/" + name)
    #     if str(value).lower() in ("yes", "y", "true",  "t", "1"):
    #         return True
    #     if str(value).lower() in ("no",  "n", "false", "f", "0", "0.0", "", "none", "[]", "{}"):
    #         return False
    #     raise Exception('Invalid value for boolean conversion: ' + str(value))

    def set(self, name, value):
        with self.pool.reserve() as mc:
            mc.set(self.code + "/" + name, value)

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

    def set_configuration(self, name, value):
        with self.pool.reserve() as mc:
            return mc.set(name, value)

    def get_configuration(self, name, value):
        with self.pool.reserve() as mc:
            return mc.get(name)


#    def get_external(self, external_code, name):
#       return self.mc.get(external_code + "/" + name)
