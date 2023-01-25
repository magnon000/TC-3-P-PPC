from multiprocessing.managers import BaseManager
import sys


class QueueManager(BaseManager):
    pass


QueueManager.register('get_queue')
manager = QueueManager(address=('127.0.0.1', 8081), authkey=b'show_me_weather')
# manager.connect()
try:
    manager.connect()
except ConnectionRefusedError:
    print('server offline')
    sys.exit()

queue = manager.get_queue()
# with manager.get_queue() as queue:
print('TEST')
print(queue.get())
