import socket
import select
import concurrent.futures
from multiprocessing import Process, Semaphore
import time

HOST = "localhost"
PORT = 1856
MAX_SIMULTANEOUS_TRANSACTIONS = 3

marche_ouvert = True
prix = 0.25

historique_transactions = []

# # abandonné : tester l'existence du serveur avant de continuer (et inscrire le client pour le serveur)
# def inscription_client(socket_inscription, addresse):
#     data = socket_inscription.recv(1024)


def guichet_client(guichet_socket, addresse, semaphore):
    print("Initiation d'une transaction avec un client sous l'addresse "+addresse)
    global historique_transactions
    with guichet_socket:
        data = guichet_socket.recv(1024)
        quantite = float(data.decode())
        time.sleep(5) # A ENELVER APRES TESTS
        with semaphore:
            facture = prix*quantite
            historique_transactions.append(facture)
        a_envoyer = str(quantite) + "|" + str(facture)
        guichet_socket.send(a_envoyer.encode())
        terminal_message = "La maison "+addresse+" a "
        terminal_message += ("ACHETÉ " if quantite > 0 else "VENDU ")+str(abs(quantite))+" kHw d'énergie pour "
        terminal_message += str(facture)+" € (unitaire: "+str(prix)+" €/kWh)"
        print(terminal_message)



if __name__ == "__main__":
    prix_semaphore = Semaphore(1)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setblocking(False)
        server_socket.bind((HOST, PORT))
        server_socket.listen(MAX_SIMULTANEOUS_TRANSACTIONS)
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_SIMULTANEOUS_TRANSACTIONS) as pool:
            while marche_ouvert:
                print("e")
                readable, writable, erreur = select.select([server_socket], [], [], 1)
                if server_socket in readable:
                    client_socket, address = server_socket.accept()
                    pool.submit(guichet_client, client_socket, str(address[1]), prix_semaphore)



