# import weather_dict
from weather import *
import time

# manager_client = weather_dict.ManagerClient(weather_dict.ADDRESS, weather_dict.PORT, weather_dict.AUTH_KEY)
manager_client = ManagerClient(ADDRESS, PORT, AUTH_KEY)
while True:
    # open_lock = manager_client.get_open_lock()
    share_dict = manager_client.get_dict()
    print(share_dict.get('temperature'))
    open_lock = manager_client.get_open_lock()
    print(open_lock)

    time.sleep(0.5)
# A reentrant lock must be released by the thread that acquired it. Once a thread has acquired a reentrant lock,
# the same thread may acquire it again without blocking;
# the thread must release it once for each time it has acquired it.
# print(share_dict.items())

