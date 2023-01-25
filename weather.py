from multiprocessing.managers import BaseManager
from queue import Queue

queue = Queue()


class QueueManager(BaseManager): pass


QueueManager.register('get_queue', callable=lambda: queue)
m = QueueManager(address=('', 50000), authkey=b'abracadabra')
s = m.get_server()
s.serve_forever()

# https://docs.python.org/3/library/multiprocessing.html#using-a-remote-manager
