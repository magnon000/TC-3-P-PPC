# import weather
from weather import *

# manager_client = weather.ManagerClient(weather.ADDRESS, weather.PORT, weather.AUTH_KEY)
manager_client = ManagerClient(ADDRESS, PORT, AUTH_KEY)
share_dict = manager_client.get_dict()
open_lock = manager_client.get_open_lock()
# print(share_dict.items())
print(share_dict.get('temperature'))
