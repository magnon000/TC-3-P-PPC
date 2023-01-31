import math
import random
import signal
import threading
import time
from multiprocessing import RLock
from multiprocessing.managers import BaseManager

PORT = 50000
ADDRESS = '127.0.0.1'
AUTH_KEY = b'weather_dict'
START_DAY = 0  # one year 360 days, choice: [0-359]


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
        global stop_weather_server
        tempe_list = build_temperature()
        day_index = 0  # begin at 01/01
        while not stop_weather_server:
            variation = random.normalvariate(0, 1.5)  # Normal distribution
            # if tempe_list[day_index] + variation > 0:
            self.items['temperature'] = tempe_list[day_index] + variation
            # else:
            #     self.items['temperature'] = 0.05
            day_index += 1
            if day_index == 360:
                day_index = 0
            time.sleep(0.2)  # time for one day
            print("day:", day_index, "; temperature:", self.items['temperature'], "°C")


class ManagerServer:
    def __init__(self, addr, port, key):
        self.address = addr
        self.port = port
        self.auth_key = key

    def start_manager_server(self):
        self.queue_manager = RemoteManager(address=('', self.port), authkey=self.auth_key)
        self.server = self.queue_manager.get_server()

    def run(self):
        self.start_manager_server()
        self.server.serve_forever()

    # def stop(self):
    # todo: stop manger server
    # self.queue_manager.shutdown()


class ManagerClient:
    def __init__(self, addr, port, key):
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
    """supposons un an a 360 jour, et la temperature varie sous forme 36 * sin(jour)"""
    tempe_list = [abs(36 * math.sin((t - START_DAY) / 36 / math.pi) + 1.2) for t in
                  range(360)]  # +1.2 pour temperature >= 0
    return tempe_list


weather_dict = WeatherDict()
# weather_dict['temperature'] = 20
# weather_dict['rain'] = True
# print(weather_dict.items)
lock = RLock()  # reentrant lock objects
# lock.acquire()
RemoteManager.register('WeatherDictInstance', callable=lambda: weather_dict)
RemoteManager.register('open_lock', callable=lambda: lock)

# stop_weather_server = threading.Event()
stop_weather_server = False
# stop_weather_server.clear()
# print(stop_weather_server)


def stop_weather(sig):
    """for main to stop weather_dict, the simplest"""
    global stop_weather_server
    if not stop_weather_server.is_set():
        if sig == signal.SIGUSR1:
            stop_weather_server.set()


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
