# import weather_dict
from weather import *
import threading


def kill(sig, _):
    print(sig)
    if sig == signal.SIGINT:
        # SERVER.stop_weather_server()
        sys.exit()


def run():
    # weather_dict.weather_dict.update_weather()
    # print(weather_dict.weather_dict.items())
    # manager_server = weather_dict.ManagerServer(weather_dict.ADDRESS, weather_dict.PORT, weather_dict.AUTH_KEY)
    manager_server = ManagerServer(ADDRESS, PORT, AUTH_KEY)
    # manager_server.run()
    # manager_server.stop()
    signal.signal(signal.SIGINT, kill)
    weather_server_thread = threading.Thread(target=manager_server.run)
    weather_server_thread.setDaemon = True
    # weather_update_thread1 = threading.Thread(target=update_weather)
    weather_update_thread1 = threading.Thread(target=weather_dict.update_weather)
    weather_update_thread1.setDaemon = True
    weather_server_thread.start()
    weather_update_thread1.start()
    # sys.exit()
    weather_update_thread1.join()
    weather_server_thread.join()


if __name__ == '__main__':
    run()
