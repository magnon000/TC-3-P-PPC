from multiprocessing.managers import BaseManager
from multiprocessing import Process, Queue, freeze_support


# https://docs.python.org/3/library/multiprocessing.html#using-a-remote-manager
class Weather(Process):
    def __init__(self, q):
        self.q = q
        super().__init__()

    def temperature(self):
        self.q.put('20')


class QueueManager(BaseManager):
    pass


if __name__ == '__main__':
    freeze_support()
    queue = Queue()

    # def task_queue():
    #     return queue

    weather = Weather(queue)
    # weather.start()
    weather.temperature()
    QueueManager.register('get_queue', callable=lambda: queue)
    # QueueManager.register('get_queue', callable=task_queue())
    manager = QueueManager(address=('', 8081), authkey=b'show_me_weather')  # empty address for localhost
    # with QueueManager(address=('', 8081), authkey=b'show_me_weather') as manager:
    server = manager.get_server()
    server.serve_forever()
    # manager.start()
    # weather.temperature()
