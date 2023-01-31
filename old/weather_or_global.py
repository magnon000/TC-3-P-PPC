from multiprocessing.managers import BaseManager  # or SyncManager: A subclass of BaseManager
# https://docs.python.org/3/library/multiprocessing.html#multiprocessing.managers.SyncManager
from multiprocessing.managers import Value
import threading  # weather is managed independently by a scheduler
import signal  # signal.SIGUSR1 & signal.SIGUSR2 for 2 events of weather
import random
import time

"""
Defining a custom Manager class that extends BaseManager.
Registering the Python class with the custom manager.
Creating an instance of the custom manager.
Creating an instance of the Python object from the manager instance.
"""

class WeatherClass:
    """custom manager, so we can add different events here"""
    def __init__(self):
        self.temperature = Value('i', 20)

    def generate_temperature(self):  # , baseline
        global stop_weather_server
        while not stop_weather_server:
            self.temperature = random.randint(1, 3)   # add a baseline
            time.sleep(1)


class WeatherManager(BaseManager):
    pass


# weather_dict = {'temperature': None,
#                 'temp_variation': None,
#                 'other': None}
server = None  # Server object
stop_weather_server = threading.Event()  # manages a flag that can be set to true with set() to false with clear()
address = "127.0.0.1"
port = 50000
weather_key = b'show_me_weather'
weather_obj = WeatherClass()
weather_obj.generate_temperature()


def return_tempe():
    return weather_obj.temperature


def start_weather():
    global server
    WeatherManager.register('show_temperature', callable=WeatherClass.generate_temperature)
    manager1 = WeatherManager(address=(address, port), authkey=weather_key)
    server = manager1.get_server()
    server.serve_forever()  # to ensure that the manager object refers to a started manager process.
    # https://stackoverflow.com/questions/44940164/stopping-a-python-multiprocessing-basemanager-serve-forever-server
    # manager1.start()  # can not
    return server


def stop_weather(sig):
    """for main to stop weather, the simplest"""
    global stop_weather_server
    if not stop_weather_server.is_set():
        if sig == signal.SIGUSR1:
            stop_weather_server.set()
        elif sig == signal.SIGUSR2:
            stop_weather_server.set()


def run_weather():
    global stop_weather_server
    weather_server_thread = threading.Thread(target=start_weather)
    weather_server_thread.start()
    print(weather_obj.temperature)
    WeatherManager.register('Weather', weather_obj)
    # with WeatherManager() as manager:  # todo： problem
    #     temperature = manager.weather_obj
    #     print(temperature.temperature.value)

    weather_server_thread.join()
# https://docs.python.org/3/library/multiprocessing.html#multiprocessing.managers.BaseManager
# https://docs.python.org/3/library/threading.html?highlight=threading%20event%20set#threading.Event.set


if __name__ == '__main__':
    run_weather()

