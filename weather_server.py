# import weather_dict
from weather import *
import threading


def run():
    # weather_dict.weather_dict.update_weather()
    # print(weather_dict.weather_dict.items())
    # manager_server = weather_dict.ManagerServer(weather_dict.ADDRESS, weather_dict.PORT, weather_dict.AUTH_KEY)
    manager_server = ManagerServer(ADDRESS, PORT, AUTH_KEY)
    # manager_server.run()
    # manager_server.stop()
    weather_server_thread = threading.Thread(target=manager_server.run)
    # weather_update_thread1 = threading.Thread(target=update_weather)
    weather_update_thread1 = threading.Thread(target=weather_dict.update_weather)
    weather_server_thread.start()
    weather_update_thread1.start()
    weather_update_thread1.join()
    weather_server_thread.join()


if __name__ == '__main__':
    run()
