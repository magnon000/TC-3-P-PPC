import time
import sys
from multiprocessing.managers import BaseManager


def start_worker(addr, port, key):
    BaseManager.register('get_task_queue')
    BaseManager.register('get_result_queue')
    client = BaseManager(address=(addr, port), authkey=key)
    try:
        client.connect()
        print('Connect to server %s' % addr)
    except ConnectionRefusedError:
        print('server offline')
        sys.exit()
    return client


def get_queue(worker):
    task = worker.get_task_queue()
    result = worker.get_result_queue()
    while True:
        if task.empty():
            time.sleep(1)
            continue
        n = task.get(timeout=1)
        print(n)
        result.put(n)
        time.sleep(1)


if __name__ == "__main__":
    client_manager = start_worker('127.0.0.1', 50000, b'show_me_weather')
    get_queue(client_manager)
