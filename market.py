import socket
import select
import concurrent.futures

HOST = "localhost"
PORT = 1856

marche_ouvert = True
prix = 0.0


def guichet_client(socket_guichet, addresse):
    return None


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.setblocking(False)
    server_socket.bind((HOST, PORT))
    server_socket.listen(4)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        while marche_ouvert:
            readable, writable, erreur = select.select([server_socket], [], [], 1)
            if server_socket in readable:
                client_socket, address = server_socket.accept()

