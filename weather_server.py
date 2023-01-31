# import weather
from weather import *
import threading


def run():
    # weather.weather.update_weather()
    # print(weather.weather.items())
    # manager_server = weather.ManagerServer(weather.ADDRESS, weather.PORT, weather.AUTH_KEY)
    manager_server = ManagerServer(ADDRESS, PORT, AUTH_KEY)
    # manager_server.run()
    # manager_server.stop()
    weather_server_thread = threading.Thread(target=manager_server.run)
    weather_update_thread1 = threading.Thread(target=update_weather)
    weather_server_thread.start()
    weather_update_thread1.start()
    weather_update_thread1.join()
    weather_server_thread.join()


if __name__ == '__main__':
    run()
