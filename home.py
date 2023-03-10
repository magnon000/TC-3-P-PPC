import socket
import os
import sys
import sysv_ipc
from multiprocessing import Process, Semaphore
import threading
import time
import random
import subprocess
import signal
from weather import *

HOST = "localhost"
PORT = 1856
MQ_CLE = 123
MQ_SEM_CLE = 124
description_types_maisons = ["I : Je donne toujours mon surplus",
                             "II : Je vends toujours mon surplus",
                             "III : Je vends mon surplus si personne n'en veut"]

# bornes min et max des configs aléatoires lorsque aucun paramètres au lancement du programme
MAX_RANDOM_ENERGIE = 100
MIN_RANDOM_ENERGIE = 0

utilise_electricite = True
conso_energie = 0
prod_energie = 0
compensation_energie = 0
benefice_energie_global = prod_energie + compensation_energie - conso_energie


# appeler dans la sémaphore energie
def maj_energie(parametre_modifie, quantite):
    global benefice_energie_global
    global compensation_energie
    global conso_energie
    global prod_energie
    quantite = float(quantite)
    if parametre_modifie == "compensation":
        compensation_energie += quantite
        print("\nMAJ COMP > Compensation électrique modifiée :", compensation_energie)
    elif parametre_modifie == "consommation":
        conso_energie += quantite
        print("\nMAJ CONSO > Consommation électrique modifiée (température) :", conso_energie)
    elif parametre_modifie == "production":
        prod_energie += quantite
        print("\nMAJ PROD > Production électrique modifiée :", prod_energie)
    else:
        print("Erreur maj_energie(): " + parametre_modifie + " non valide")
    benefice_energie_global = round(prod_energie + compensation_energie - conso_energie, 5)
    print("MAJ BENEFICE > Benefice électrique maintenant à", benefice_energie_global, "kWh\n")


# pas tout en 1 seule semaphore car la connection au serveur peut prendre du temps ça ralentirait tout
# De toutes façons c'est raisonable de considérer qu'il puisse y avoir des changemetns entre le moment où
# l'utilisateur se décide d'aller acheter et le moment où il aboutit l'achat d'électricité
# => l'achat ne doit pas être atomique
def achat_market(manque):
    print("\nMARCHÉ > Déficit d'énergie de " + str(
        manque) + " kWh. \nInitiation d'une transaction avec le marché pour en acheter.")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as market_achat_socket:
        try:
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
            prix_a_payer = facture[pos_separateur + 1:]
            print("\nFacture (quantité reçue | prix à payer):", quantite_recue, "kWh |", prix_a_payer, "€")
            with energie_semaphore:
                maj_energie("compensation", quantite_recue)
        except ConnectionRefusedError:
            print("ERREUR: impossible de se connecter au marché. Il n'est sûrement pas ouvert. Termination")
            global utilise_electricite
            utilise_electricite = False


def vente_market(a_vendre):
    print("\nMARCHÉ > Surplus d'énergie de " + str(
        a_vendre) + " kWh. \nInitiation d'une transaction avec le marché pour le vendre.")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as market_vente_socket:
        try:
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
        except ConnectionRefusedError:
            print("ERREUR: connection au marché impossible. Il n'est sûrement pas ouvert. Termination.")
            global utilise_electricite
            utilise_electricite = False


def don_voisinnage(a_donner):
    a_donner = str(a_donner)
    print("\nDONS > Surplus d'énergie de " + a_donner + " kWh. Don au voisinnage.\n")
    message = a_donner.encode()
    mq_saturation = False
    with queue_semaphore:
        try:
            dons_mq.send(message, type=pid)
        except sysv_ipc.BusyError:
            mq_saturation = True

    if mq_saturation:
        print("ESPACE DE DONS SATURÉ: vente sur le marché, malheureusement je n'ai pas le choix...")
        vente_market(a_donner)
    else:
        with energie_semaphore:
            maj_energie("compensation", -float(a_donner))


def don_voisinnage_ou_vente(a_donner):
    a_donner = str(a_donner)
    print("\nDONS > Surplus d'énergie de " + a_donner + " kWh. Initiation d'un don au voisinnage...\n")
    message = a_donner.encode()
    mq_saturation = False
    with queue_semaphore:
        try:
            dons_mq.send(message, type=pid)
        except sysv_ipc.BusyError:
            mq_saturation = True

    if mq_saturation:
        print("ESPACE DE DONS SATURÉ: vente sur le marché à la place !")
        vente_market(a_donner)
    else:
        time.sleep(3)
        personne_ne_veut = True
        with queue_semaphore:
            try:
                dons_mq.receive(block=False, type=pid)
            except sysv_ipc.BusyError:
                personne_ne_veut = False
        if personne_ne_veut:
            print("Aucun prenneur parmis les voisins. Le surplus sera vendu au marché.")
            vente_market(a_donner)
        else:
            with energie_semaphore:
                maj_energie("compensation", -float(a_donner))
            print("Le surplus a bien été donné au voisinnage.")


def recolte_don(manque):
    print("\nDONS > Déficit d'énergie de " + str(manque) + " kWh. Recherche de dons du voisinnage...\n")
    quantite_recoltee = 0
    don_dernier_tour = True

    # si on veut passer au mode chacun son tour : intervertir sémaphore et while
    with queue_semaphore:
        while quantite_recoltee < manque and don_dernier_tour:
            try:
                message, type_msg = dons_mq.receive(block=False)
                quantite_recoltee += float(message.decode())
            except sysv_ipc.BusyError:
                # arrêter la récolte lorsqu'il n'y a plus de dons dans la message queue
                don_dernier_tour = False

    print("DONS > Obtenu", quantite_recoltee, "kWh par donation(s).")
    if quantite_recoltee > 0:
        with energie_semaphore:
            maj_energie("compensation", quantite_recoltee)

    return quantite_recoltee - manque


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


def formule_conso(temperature, conso, rain):
    if rain:
        return conso + conso * 0.0005 * ((2 * temperature - 34) ** 2) * 1.2  # 1.2 rain coef
    else:
        return conso + conso * 0.0005 * ((2 * temperature - 34) ** 2)


def evolution_conso():
    global conso_energie
    connected = False
    manager_client = ManagerClient('127.0.0.1', 50000, b'weather_dict')
    share_dict = manager_client.get_dict()
    conso_initiale = conso_energie
    ancienne_temperature = 0
    temperature = share_dict.get('temperature')
    while utilise_electricite:
        share_dict = manager_client.get_dict()
        ancienne_temperature = temperature
        temperature = share_dict.get('temperature')
        rain = share_dict.get('rain')

        if ancienne_temperature != temperature:
            with energie_semaphore:
                nouvelle_conso = formule_conso(temperature, conso_initiale, rain)
                maj_energie("consommation", nouvelle_conso - conso_energie)


def separateur():
    print("-----------------------------------")


def get_nb_autre_homes():
    commande_verif = 'ps -ef | grep "home.py" | grep -v grep | wc -l'
    proc = subprocess.Popen(commande_verif, stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    nb_maisons = int(out.decode())
    return nb_maisons


def flush_message_queue_if_necessary():
    # supprimer la message queue de l'ancienne session si elle existe encore
    if get_nb_autre_homes() < 2:
        try:
            a_supprimer = sysv_ipc.MessageQueue(MQ_CLE)
            a_supprimer.remove()
        except sysv_ipc.ExistentialError:
            pass


def delete_semaphore_if_necessary():
    if get_nb_autre_homes() < 2:
        try:
            a_supprimer = sysv_ipc.Semaphore(MQ_SEM_CLE)
            a_supprimer.remove()
        except sysv_ipc.ExistentialError:
            pass


def termination(sig, frame):
    if sig == signal.SIGINT:
        global utilise_electricite
        utilise_electricite = False
        global dons_mq
        with queue_semaphore:
            flush_message_queue_if_necessary()
        delete_semaphore_if_necessary()
        print("Demande de termination. La maison se détruira dès que possible.")


if __name__ == "__main__":

    queue_semaphore = sysv_ipc.Semaphore(MQ_SEM_CLE, flags=sysv_ipc.IPC_CREAT, initial_value=1)
    with queue_semaphore:
        flush_message_queue_if_necessary()
    dons_mq = sysv_ipc.MessageQueue(MQ_CLE, sysv_ipc.IPC_CREAT)
    pid = os.getpid()
    if len(sys.argv) < 4:
        print("AVERTISSEMENT: la configuration de départ de la maison n'a pas été spécifiée."
              "Des valeurs aléatoires seront attribuées.")
        type_maison = random.randint(1, 3)
        prod_energie = float(random.randint(MIN_RANDOM_ENERGIE, MAX_RANDOM_ENERGIE))
        conso_energie = float(random.randint(MIN_RANDOM_ENERGIE, MAX_RANDOM_ENERGIE))
    else:
        type_maison = int(sys.argv[1])
        prod_energie = float(sys.argv[2])
        conso_energie = float(sys.argv[3])

    signal.signal(signal.SIGINT, termination)

    # remote manager
    thread_conso = threading.Thread(target=evolution_conso)
    thread_conso.start()

    separateur()
    print("Je suis la maison", os.getpid(), "de type", description_types_maisons[type_maison - 1])
    print("Ma production initiale est de", prod_energie, "kWh et ma consommation initiale est de ", conso_energie,
          "kWh.")
    separateur()

    benefice_energie_global = prod_energie + compensation_energie - conso_energie
    energie_semaphore = Semaphore(1)
    thread_achat = threading.Thread(target=acquisition_energie)
    thread_achat.start()
    thread_vente = threading.Thread(target=separation_energie)
    thread_vente.start()
    thread_vente.join()
    thread_achat.join()
    thread_conso.join()
