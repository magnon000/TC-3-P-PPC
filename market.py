import socket
import select
import concurrent.futures
from multiprocessing import Process, Semaphore

HOST = "localhost"
PORT = 1856
MAX_SIMULTANEOUS_TRANSACTIONS = 5

marche_ouvert = True
prix = 0.0

historique_transactions = []

# # abandonné : tester l'existence du serveur avant de continuer (et inscrire le client pour le serveur)
# def inscription_client(socket_inscription, addresse):
#     data = socket_inscription.recv(1024)


def guichet_client(guichet_socket, addresse, semaphore):
    global historique_transactions
    with guichet_socket:
        data = guichet_socket.recv(1024)
        quantite = float(data.decode()[0])
        with semaphore:
            facture = prix*quantite
            historique_transactions.append(-facture)
        guichet_socket.send(str(-quantite) + "|" + str(facture))
        terminal_message = "La maison "+addresse+" a "
        terminal_message += ("ACHETÉ " if quantite<0 else "VENDU ")+str(quantite)+" kHw d'énergie pour "
        terminal_message += str(facture)+" € (unitaire: "+str(prix)+" €/kWh)"




if __name__ == "__main__":
    prix_semaphore = Semaphore(1)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setblocking(False)
        server_socket.bind((HOST, PORT))
        server_socket.listen(MAX_SIMULTANEOUS_TRANSACTIONS)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            while marche_ouvert:
                readable, writable, erreur = select.select([server_socket], [], [], 1)
                if server_socket in readable:
                    client_socket, address = server_socket.accept()
                    pool.submit(guichet_client, [client_socket, address, prix_semaphore])
