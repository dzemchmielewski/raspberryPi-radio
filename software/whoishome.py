import io
import os
import subprocess

from confidential.phones_ip import PHONES
from bus import Bus
from entities import RadioItem, WHOISHOME_CONTROLLER_LOG, now, SECOND


class WhoIsHomeController(RadioItem):
    CODE = "whoishome_ctrl"

    def __init__(self):
        super(WhoIsHomeController, self).__init__(Bus(WHOISHOME_CONTROLLER_LOG, WhoIsHomeController.CODE), loop_sleep=2)
        self.last_check = None
        self.hosts = PHONES
        self.last_result = [-1] * 4
        self.confirm_change_status = [0] * 4

    @staticmethod
    def ping(host):
        with io.open(os.devnull, 'wb') as devnull:
            try:
                subprocess.check_call(
                    ['ping', '-c1', host],
                    stdout=devnull, stderr=devnull)
            except subprocess.CalledProcessError:
                return 0
            else:
                return 1

    def loop(self):
        if self.last_check is None or now() > self.last_check + (10*SECOND):
            for i in range(len(self.hosts)):
                result = self.ping(self.hosts[i][1])
                if self.last_result[i] != result:
                    self.confirm_change_status[i] += 1
                    if self.confirm_change_status[i] >= 5:
                        self.bus.log("{}    {} -> {}".format(self.hosts[i][0], self.last_result[i], result))
                        self.last_result[i] = result
                        self.confirm_change_status[i] = 0
                else:
                    self.confirm_change_status[i] = 0
            self.last_check = now()

    def exit(self):
        pass
