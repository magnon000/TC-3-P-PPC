import socket
import os
import sys
import sysv_ipc
from multiprocessing import Process, Semaphore
import threading

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
    print("Surplus d'énergie de " + str(a_vendre) + " kWh. Initiation d'une transaction avec le marché pour le vendre")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as market_vente_socket:
        market_vente_socket.connect((HOST, PORT))
        quantite_a_vendre= str(a_vendre)
        market_vente_socket.send(quantite_a_vendre.encode())
        reponse = market_vente_socket.recv(1024)
        if not len(reponse):
            print("ERREUR: la connection au marché est fermée")
            sys.exit(1)
        fiche_de_paie = reponse.decode()
        pos_separateur = fiche_de_paie.index("|")
        quantite_vendue = fiche_de_paie[:pos_separateur]
        revenus = fiche_de_paie[pos_separateur + 1:]
        print("Facture (quantité vendue | profit):", quantite_vendue, "|", revenus, "€")
        with energie_semaphore:
            maj_energie("compensation", -float(quantite_vendue))



if __name__ == "__main__":
    type_maison = int(sys.argv[1])
    print("Je suis la maison", os.getpid(), "de type",description_types_maisons[type_maison-1])
    energie_semaphore = Semaphore(1)
    while utilise_electricite:
        with energie_semaphore:
            benefice = benefice_energie_global
        if benefice < 0:
            manque_energie = -benefice
            thread_achat = threading.Thread(target=achat_market, args=[manque_energie])
            thread_achat.start()
            thread_achat.join()
        elif benefice > 0:
            if type_maison == 2:
                surplus_energie = benefice
                thread_vente = threading.Thread(target=vente_market, args=[surplus_energie])
                thread_vente.start()
                thread_vente.join()

