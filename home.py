import socket
import os
import sys
import sysv_ipc
from multiprocessing import Process, Semaphore
import threading
import time

HOST = "localhost"
PORT = 1856
MQ_CLE = 123
description_types_maisons = ["I : Je donne toujours mon surplus",
                             "II : Je vends toujours mon surplus",
                             "III : Je vends mon surplus si personne n'en veut"]

homes_mq = sysv_ipc.MessageQueue(MQ_CLE, sysv_ipc.IPC_CREAT)

utilise_electricite = True
conso_energie = float(sys.argv[2])
prod_energie = float(sys.argv[3])
compensation_energie = 0
benefice_energie_global = prod_energie+compensation_energie-conso_energie


# appeler dans la sémaphore energie
def maj_energie(parametre_modifie, quantite):
    global benefice_energie_global
    global compensation_energie
    global conso_energie
    global prod_energie
    quantite = float(quantite)
    if parametre_modifie == "compensation":
        compensation_energie += quantite
        print("Compensation électrique maintenant à", compensation_energie)
    elif parametre_modifie == "consommation":
        conso_energie += quantite
        print("Consommation électrique maintenant à", conso_energie)
    elif parametre_modifie == "production":
        prod_energie += quantite
        print("Production électrique maintenant à", prod_energie)
    else:
        print("Erreur maj_energie(): "+parametre_modifie+" non valide")
    benefice_energie_global = prod_energie+compensation_energie-conso_energie
    print("Benefice électrique maintenant à", benefice_energie_global, "kWh")


# pas tout en 1 seule semaphore car la connection au serveur peut prendre du temps ça ralentirait tout
# De toutes façons c'est raisonable de considérer qu'il puisse y avoir des changemetns entre le moment où
# l'utilisateur se décide d'aller acheter et le moment où il aboutit l'achat d'électricité
# => l'achat ne doit pas être atomique
def achat_market(manque):
    print("Déficit d'énergie de "+str(manque)+" kWh. Initiation d'une transaction avec le marché pour en acheter.")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as market_achat_socket:
        market_achat_socket.connect((HOST, PORT))
        quantite_demandee = str(manque)
        market_achat_socket.send(quantite_demandee.encode())
        reponse = market_achat_socket.recv(1024)
        if not len(reponse):
            print("ERREUR: la connection au marché est fermée")
            sys.exit(1)
        facture = reponse.decode()
        pos_separateur = facture.index("|")
        quantite_recue = facture[:pos_separateur]
        prix_a_payer = facture[pos_separateur+1:]
        print("Facture (quantité reçue | prix à payer):", quantite_recue, "|", prix_a_payer, "€")
        with energie_semaphore:
            maj_energie("compensation", quantite_recue)


def vente_market(a_vendre):
    print("Surplus d'énergie de " + str(a_vendre) + " kWh. Initiation d'une transaction avec le marché pour le vendre.")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as market_vente_socket:
        market_vente_socket.connect((HOST, PORT))
        quantite_a_vendre = str(-float(a_vendre))
        market_vente_socket.send(quantite_a_vendre.encode())
        reponse = market_vente_socket.recv(1024)
        if not len(reponse):
            print("ERREUR: la connection au marché est impossible")
            sys.exit(1)
        fiche_de_paie = reponse.decode()
        pos_separateur = fiche_de_paie.index("|")
        quantite_vendue = fiche_de_paie[:pos_separateur]
        revenus = fiche_de_paie[pos_separateur + 1:]
        print("Revenus (quantité d'énergie | profit):", quantite_vendue, "kWh |", revenus, "€")
        with energie_semaphore:
            maj_energie("compensation", float(quantite_vendue))


def don_voisinnage(a_donner):
    a_donner = str(a_donner)
    print("Surplus d'énergie de " + a_donner + " kWh. Don au voisinnage.")
    message = a_donner.encode()
    with queue_semaphore:
        homes_mq.send(message, type=pid)
    with energie_semaphore:
        maj_energie("compensation", -float(a_donner))


def don_voisinnage_ou_vente(a_donner):
    a_donner = str(a_donner)
    print("Surplus d'énergie de " + a_donner + " kWh. Initiation d'un don au voisinnage...")
    message = a_donner.encode()
    with queue_semaphore:
        homes_mq.send(message, type=pid)
    time.sleep(3)
    personne_ne_veut = True
    with queue_semaphore:
        try:
            homes_mq.receive(block=False, type=pid)
        except sysv_ipc.BusyError:
            personne_ne_veut = False
    if personne_ne_veut:
        print("Aucun prenneur parmis les voisins. Le surplus sera vendu au marché.")
        vente_market(a_donner)
    else:
        with energie_semaphore:
            maj_energie("compensation", -a_donner)
        print("Le surplus a bien été donné au voisinnage.")


def recolte_don(manque):
    print("Déficit d'énergie de "+str(manque)+" kWh. Recherche de dons du voisinnage...")
    quantite_recoltee = 0
    don_dernier_tour = True

    # si on veut passer au mode chacun son tour : intervertir sémaphore et while
    with queue_semaphore:
        while quantite_recoltee < manque and don_dernier_tour:
            try:
                message = homes_mq.receive(block=False, type=pid)
                quantite_recoltee += int(message.decode())
            except sysv_ipc.BusyError:
                # arrêter la récolte lorsqu'il n'y a plus de dons dans la message queue
                don_dernier_tour = False

    if quantite_recoltee > 0:
        with energie_semaphore:
            maj_energie("compensation", quantite_recoltee)
    print("Obtenu", quantite_recoltee, "kWh par donation(s).")

    return quantite_recoltee-manque


# thread qui détecte et gère les surplus d'énergie selon la politique de la maison
def separation_energie():
    while utilise_electricite:
        with energie_semaphore:
            benefice = benefice_energie_global
        if benefice > 0:
            surplus = benefice
            if type_maison == 2:
                vente_market(surplus)
            elif type_maison == 1:
                don_voisinnage(surplus)
            elif type_maison == 3:
                don_voisinnage_ou_vente(surplus)


# thread qui détecte et gère les acquisitions d'énergie
def acquisition_energie():
    while utilise_electricite:
        with energie_semaphore:
            benefice = benefice_energie_global
        if benefice < 0:
            manque = -benefice
            benefice_apres_don = recolte_don(manque)
            # car après la recolte de dons, si le benefice est encore négatif, il faut acheter au marché
            # (s'il est positif, le thread separation le verra et s'en occupera)
            if benefice_apres_don < 0:
                manque_apres_don = -benefice_apres_don
                print("Les dons n'ont pas suffit, il manque ", manque_apres_don, " kWh.")
                achat_market(manque_apres_don)


if __name__ == "__main__":
    pid = os.getpid()
    type_maison = int(sys.argv[1])
    print("Je suis la maison", os.getpid(), "de type", description_types_maisons[type_maison-1])
    energie_semaphore = Semaphore(1)
    queue_semaphore = Semaphore(1)
    thread_achat = threading.Thread(target=acquisition_energie)
    thread_achat.start()
    thread_vente = threading.Thread(target=separation_energie)
    thread_vente.start()
    thread_vente.join()
    thread_achat.join()

