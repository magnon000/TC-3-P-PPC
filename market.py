import socket
import select
import concurrent.futures
from multiprocessing import Process, Semaphore
import time
import signal
import sys
import random

HOST = "localhost"
PORT = 1856
MAX_SIMULTANEOUS_TRANSACTIONS = 3

marche_ouvert = True
prix = 0
prix_precedent = 0

historique_transactions = []

# # abandonné : tester l'existence du serveur avant de continuer (et inscrire le client pour le serveur)
# def inscription_client(socket_inscription, addresse):
#     data = socket_inscription.recv(1024)


def guichet_client(guichet_socket, addresse, semaphore):
    print("Initiation weather'une transaction avec un client sous l'addresse "+addresse)
    global historique_transactions
    with guichet_socket:
        data = guichet_socket.recv(1024)
        quantite = float(data.decode())
        time.sleep(5)  # A ENELVER APRES TESTS
        with semaphore:
            facture = prix*quantite
            historique_transactions.append(facture)
        a_envoyer = str(quantite) + "|" + str(facture)
        guichet_socket.send(a_envoyer.encode())
        terminal_message = "La maison de la transaction "+addresse+" a "
        terminal_message += ("ACHETÉ " if quantite > 0 else "VENDU ")+str(abs(quantite))+" kHw weather'énergie pour "
        terminal_message += str(facture)+" € (unitaire: "+str(prix)+" €/kWh)"
        print(terminal_message)


def termination(sig, frame):
    if sig == signal.SIGINT:
        global marche_ouvert
        marche_ouvert = False
        print("Demande de termination. Le marché se fermera dès que possible.")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("AVERTISSEMENT: la configuration de départ du marché n'a pas été spécifiée."
              "Des valeurs aléatoires seront attribuées.")
        prix_initial = round(random.uniform(0.05, 10.0), 2)  # entre 5 centime et 10€ au kWh
        gamme_coef = round(random.uniform(0.0, 1.0), 2)
        contribution_mouvements_marche = round(random.uniform(0.0, 1.0), 2)
    else:
        prix_initial = float(sys.argv[1])
        gamme_coef = float(sys.argv[2])
        contribution_mouvements_marche = float(sys.argv[3])

    signal.signal(signal.SIGINT, termination)
    signal.signal(signal.SIGINT, termination)
    prix_semaphore = Semaphore(1)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setblocking(False)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(MAX_SIMULTANEOUS_TRANSACTIONS)
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_SIMULTANEOUS_TRANSACTIONS) as pool:
            while marche_ouvert:
                print(historique_transactions)
                readable, writable, erreur = select.select([server_socket], [], [], 1)
                if server_socket in readable:
                    client_socket, address = server_socket.accept()
                    pool.submit(guichet_client, client_socket, str(address[1]), prix_semaphore)

        # peut être pas utile vu qu'il y a le with
        server_socket.shutdown(socket.SHUT_RDWR)
        server_socket.close()


