import socket
import os
import sys
import sysv_ipc
from multiprocessing import Process, Semaphore

HOST = "localhost"
PORT = 1856
MQ_KEY = 123

homes_mq = sysv_ipc.MessageQueue(MQ_KEY, sysv_ipc.IPC_CREAT)

conso_energie = float(sys.argv[2])
prod_energie = float(sys.argv[3])
benefice_energie = prod_energie-conso_energie

def achat_market(semaphore):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as market_socket:
        market_socket.connect((HOST, PORT))
        if m == 1:
            market_socket.send(b"1")
            resp = market_socket.recv(1024)
            if not len(resp):
                print("The socket connection has been closed!")
                sys.exit(1)
            print("Server response:", resp.decode())
        if m == 2:
            market_socket.send(b"2")
        with semaphore:
            quantite_demandee = benefice_energie
        market_socket.send(quantite_demandee.encode())




if __name__ == "__main__":
    print("Je suis la maison",os.getpid(),"de type",sys.argv[1])
