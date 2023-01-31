import socket
import select
import concurrent.futures
from multiprocessing import Process, Semaphore
import time
import signal
import sys
import random
import threading
import os

HOST = "localhost"
PORT = 1856
MAX_SIMULTANEOUS_TRANSACTIONS = 3

marche_ouvert = True
prix = 0.00
prix_precedent = 0.00

# du point de vue du marché (=> achat = le marché à acheté à une maison, inversement pour vente)
historique_ventes = []
historique_achats = []
NOMBRE_TRANSACTIONS_UTILES = 5
MODULATION_HISTORIQUE_DEFAULT = 0.001

# # abandonné : tester l'existence du serveur avant de continuer (et inscrire le client pour le serveur)
# def inscription_client(socket_inscription, addresse):
#     data = socket_inscription.recv(1024)


def guichet_client(guichet_socket, addresse, semaphore):
    print("Initiation d'une transaction avec un client sous l'addresse "+addresse)
    global historique_ventes
    global historique_achats
    terminal_message = ""
    with guichet_socket:
        data = guichet_socket.recv(1024)
        quantite = float(data.decode())
        time.sleep(3)  # A ENELVER APRES TESTS
        with semaphore:
            facture = round(prix*quantite, 5)
            if quantite > 0:
                historique_ventes.append(abs(facture))
                historique_achats.append(0.0)
            else:
                historique_ventes.append(0.0)
                historique_achats.append(abs(facture))
        a_envoyer = str(quantite) + "|" + str(abs(facture))
        guichet_socket.send(a_envoyer.encode())
        terminal_message += "La maison de la transaction "+addresse+" a "
        terminal_message += ("ACHETÉ " if quantite > 0 else "VENDU ")+str(abs(quantite))+" kHw d'énergie pour "
        terminal_message += str(abs(facture))+" € (unitaire: "+str(prix)+" €/kWh)"
        print(terminal_message)


def contribution_historique():
    nb_transactions = len(historique_achats)  # égal à historique_ventes puisque remplissage avec zéros

    # éviter que au cours du temps les transactions aient de moins en moins d'impact sur le prix en ne considérant
    # que les NOMBRE_TRANSACTIONS_UTILES dernières transactions
    if nb_transactions > NOMBRE_TRANSACTIONS_UTILES:
        somme_achats_recents = sum(historique_achats[nb_transactions-NOMBRE_TRANSACTIONS_UTILES-5:])
        somme_ventes_recentes = sum(historique_ventes[nb_transactions - NOMBRE_TRANSACTIONS_UTILES-5:])
    else:
        somme_achats_recents = sum(historique_achats)
        somme_ventes_recentes = sum(historique_ventes)

    # éviter la division par zero
    if somme_ventes_recentes > 0 or somme_achats_recents > 0:
        facteur = (somme_ventes_recentes - somme_achats_recents) / (somme_ventes_recentes + somme_achats_recents)
    else:
        facteur = 0

    return facteur


def evolution_prix():
    global marche_ouvert
    while marche_ouvert:
        time.sleep(0.5)
        with prix_semaphore:
            global prix
            global prix_precedent
            prix_precedent = prix
            prix = gamma_coef * prix_precedent + modulation_historique*contribution_historique()
            prix = round(prix, 5)
            if prix < 0:
                marche_ouvert = False
                print("ERREUR: prix de l'énergie négatif. Effondrement du marché. Changer modulation")


def termination(sig, frame):
    if sig == signal.SIGINT:
        global marche_ouvert
        marche_ouvert = False
        os.kill(pid_external, signal.SIGINT)
        print("Demande de termination. Le marché se fermera dès que possible.")


# Processus external, fils de market
def external():
    monde_existe = True

    def stop_handler(sig, frame):
        if sig == signal.SIGINT:
            nonlocal monde_existe
            monde_existe = False

    signal.signal(signal.SIGINT, stop_handler)

    strike_event = False
    antinuclear_event = False
    while monde_existe:
        destin = random.uniform(0, 1)
        if 0.000000001 < destin < 0.000000002 and not antinuclear_event:
            antinuclear_event = True
            print("Nuke on")
        if 0.10000001 < destin < 0.10000002 and antinuclear_event:
            antinuclear_event = False
            print("Nuke off")
        if 0.20000001 < destin < 0.20000002 and not strike_event:
            strike_event = True
            print("Strike on")
        if 0.30000001 < destin < 0.30000005 and strike_event:
            strike_event = False
            print("Strike off")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("AVERTISSEMENT: la configuration de départ du marché n'a pas été spécifiée."
              "Des valeurs aléatoires et par défaut seront attribuées.")
        prix_initial = round(random.uniform(0.05, 10.0), 2)  # entre 5 centime et 10€ au kWh
        gamma_coef = round(random.uniform(0.95, 0.99), 2)
        modulation_historique = MODULATION_HISTORIQUE_DEFAULT
    else:
        prix_initial = float(sys.argv[1])
        gamma_coef = float(sys.argv[2])
        modulation_historique = float(sys.argv[3])

    print("Prix initial =", prix_initial, "€/kWh | Ɣ = ", gamma_coef, "Modulation historique = ", modulation_historique)
    prix = prix_initial
    prix_semaphore = Semaphore(1)
    historique_semaphore = Semaphore(1)
    thread_prix = threading.Thread(target=evolution_prix)
    thread_prix.start()

    external_process = Process(target=external)
    external_process.start()
    pid_external = external_process.pid

    signal.signal(signal.SIGINT, termination)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setblocking(False)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(MAX_SIMULTANEOUS_TRANSACTIONS)
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_SIMULTANEOUS_TRANSACTIONS) as pool:
            while marche_ouvert:
                print("   Achats:",historique_achats, "\n   Ventes:", historique_ventes)
                print("Prix de l'énergie: ",prix)  # juste indicateur visuel => pas besoin de semaphore
                readable, writable, erreur = select.select([server_socket], [], [], 1)
                if server_socket in readable:
                    client_socket, address = server_socket.accept()
                    pool.submit(guichet_client, client_socket, str(address[1]), prix_semaphore)

        # peut être pas utile vu qu'il y a le with
        server_socket.shutdown(socket.SHUT_RDWR)
        server_socket.close()
    thread_prix.join()
    external_process.join()


