import math
import random
import signal
import threading
import time
from multiprocessing import RLock
from multiprocessing.managers import BaseManager
import sys

PORT = 50000
ADDRESS = '127.0.0.1'
AUTH_KEY = b'weather_dict'
START_DAY = 0  # one year 360 days, choice: [0-359]
SERVER = None


class RemoteManager(BaseManager):
    pass


class WeatherDict:
    def __init__(self, ):
        self.items = dict()

    def set(self, key, value):
        self.items[key] = value

    def get(self, key):
        return self.items.get(key)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        """
        Called to implement assignment to self[key]. ex. s['temp'] = 20
        This should only be implemented for mappings if the objects support changes to the values for keys,
        or if new keys can be added, or for sequences if elements can be replaced.
        shared dictionary OK.
        """
        self.set(key, value)

    def update_weather(self):
        # global SERVER
        tempe_list = build_temperature()
        day_index = 0  # begin at 01/01
        while not stop_manager_signal.is_set():
            variation = random.normalvariate(0, 1.5)  # Normal distribution
            # if tempe_list[day_index] + variation > 0:
            self.items['temperature'] = tempe_list[day_index] + variation
            # else:
            #     self.items['temperature'] = 0.05
            day_index += 1
            if day_index == 360:
                day_index = 0
                print("------new year------")
            time.sleep(0.2)  # time for one day
            print("day:", day_index, "; temperature:", self.items['temperature'], "°C")
            if day_index == 20:
                stop_weather_signal(signal.SIGINT)
        print("update_end")


def stop_weather_server():  # deadlock
    global stop_manager_signal, SERVER
    SERVER.stop_manager_signal.set()


class ManagerServer:
    def __init__(self, addr, port, key):
        self.address = addr
        self.port = port
        self.auth_key = key
        self.queue_manager = None

    def start_manager_server(self):
        global SERVER
        self.queue_manager = RemoteManager(address=('', self.port), authkey=self.auth_key)
        SERVER = self.queue_manager.get_server()

    def run(self):
        global SERVER
        self.start_manager_server()
        SERVER.serve_forever()


class ManagerClient:
    def __init__(self, addr, port, key):
        self.open_lock = None
        self.address = addr
        self.port = port
        self.auth_key = key
        self.info_manager = RemoteManager(address=(self.address, self.port), authkey=self.auth_key)
        self.info_manager.connect()

    def get_dict(self):
        # self.dict = self.info_manager.dict()
        return self.info_manager.WeatherDictInstance()

    def get_open_lock(self):
        self.open_lock = self.info_manager.open_lock()
        return self.open_lock


def build_temperature() -> list:  # baseline temperature
    """supposons qu'un an a 360 jours, et la température varie sous forme 36 * sin(jour)"""
    tempe_list = [abs(36 * math.sin((t - START_DAY) / 36 / math.pi) + 1.2) for t in
                  range(360)]  # +1.2 pour temperature >= 0
    return tempe_list


def stop_weather_signal(sig):
    """for main to stop weather_dict, the simplest"""
    # global stop_manager_signal, SERVER
    # if not stop_manager_signal.is_set():
    #     if sig == signal.SIGINT:
    #         stop_manager_signal.set()
    #         SERVER.stop_manager_signal.set()
    if sig == signal.SIGINT:
        sys.exit()


weather_dict = WeatherDict()
# weather_dict['temperature'] = 20
# weather_dict['rain'] = True
# print(weather_dict.items)

lock = RLock()  # reentrant lock objects
# lock.acquire()

RemoteManager.register('WeatherDictInstance', callable=lambda: weather_dict)
RemoteManager.register('open_lock', callable=lambda: lock)

stop_manager_signal = threading.Event()
stop_manager_signal.clear()
# print(stop_manager_signal)


# def update_weather():
#     global stop_weather_server
#     tempe_list = build_temperature()
#     day_index = 0  # begin at 01/01
#     while not stop_weather_server:
#         # print(day_index)
#         weather_dict['temperature'] = tempe_list[day_index]
#         day_index += 1
#         if day_index == 360:
#             day_index = 0
#         time.sleep(0.2)
#         print(weather_dict['temperature'])


if __name__ == "__main__":
    # pass
    # print(build_temperature())
    weather_update_thread = threading.Thread(target=weather_dict.update_weather)
    weather_update_thread.start()
    weather_update_thread.join()
