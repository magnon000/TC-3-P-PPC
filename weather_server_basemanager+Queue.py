"""https://docs.python.org/3/library/multiprocessing.html#using-a-remote-manager"""
from multiprocessing.managers import BaseManager
from multiprocessing import Process, Queue, freeze_support
import time
# from multiprocessing import shared_memory # version 3.7
# import sysv_ipc


task_queue = Queue()
result_queue = Queue()


# BaseManager.register('get_task_queue', callable=lambda: task_queue)
# AttributeError: Can't pickle local object 'start_manager.<locals>.<lambda>'
# idk why pickle can't serialize lambda
def get_task_queue():
    global task_queue
    return task_queue


def get_result_queue():
    global result_queue
    return result_queue


class Weather(Process):
    def __init__(self, q):  # q: queue
        self.q = q
        super().__init__()

    def temperature(self):
        self.q.put('20')


class QueueManager(BaseManager):
    pass


def start_manager(port: int, key, addr: str = ''):
    QueueManager.register('get_task_queue', callable=get_task_queue)
    QueueManager.register('get_result_queue', callable=get_result_queue)
    manager1 = QueueManager(address=(addr, port), authkey=key)
    # server = manager1.get_server()
    # server.serve_forever()
    # https://stackoverflow.com/questions/44940164/stopping-a-python-multiprocessing-basemanager-serve-forever-server
    # manager1.start()
    return manager1


if __name__ == '__main__':
    # freeze_support()
    manager = start_manager(50000, b'show_me_weather', addr='')
    # while True:
    #     weather = Weather(task_queue)
    #     weather.temperature()
    #     print("onerun")
    #     time.sleep(1)
    weather = Weather(task_queue)
    weather.temperature()
    server = manager.get_server()
    server.serve_forever()
    # print(result_queue.get())
    # manager.shutdown()
