import os
from multiprocessing import Process
import signal
import time
import subprocess
import sys
import sysv_ipc


def stop_handler(sig, frame):
    if sig == signal.SIGINT:
        send_end_signals()
        sys.exit()


def send_end_signals():
    processes = ["home.py", "market.py", "weather.py", "weather_server.py"]
    for process_name in processes:
        command = "ps -ef | grep " + process_name + " | grep -v grep | awk '{print $2}'"
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        liste_pids_homes = out.decode().split("\n")
        liste_pids_homes = list(filter(None, liste_pids_homes))
        for home in liste_pids_homes:
            os.kill(int(home), signal.SIGINT)


if __name__ == "__main__":

    # problème non résolu, défaite complète : message queue qui ne se supprime pas par flush lorsqu'on utilise
    # le launcher (nb de maisons >2 même au début). Donc je le fais manuellement ici...
    a_supp = sysv_ipc.MessageQueue(123, sysv_ipc.IPC_CREAT)
    a_supp.remove()


    signal.signal(signal.SIGINT, stop_handler)
    path = os.path.abspath(os.path.dirname(__file__))

    DEFAULT_VALUES = {""}

    print("\n\n\n---------------------------------------\n")
    print("PPC: SIMULATION MULTIPROCESS ET MULTITHREAD\n")
    print("---------------------------------------\n\n\n")

    entree1_erronee = True
    while entree1_erronee:
        try:
            nb_homes = int(input("Combien de maisons générer ?\n==> "))
            if nb_homes < 1:
                print("ERREUR: Au moins 1 maison nécessaire\n")
            else:
                entree1_erronee = False
        except ValueError:
            print("ERREUR: Entrer un entier")

    print("\nChoisir un mode de génération :")
    print("    1. Automatique (valeurs par défaut & aléatoires)\n    2. Personnalisé\n")

    entree2_erronee = True
    while entree2_erronee:
        try:
            mode = int(input("==> "))
            if mode != 1 and mode != 2:
                print("ERREUR: choisir une option valide......")
            else:
                entree2_erronee = False
        except ValueError:
            print("ERREUR: entrer un entier......")

    if mode == 1:
        os.system("gnome-terminal --geometry 60x30 -- python3 " + path + "/market.py")
        for i in range(0, nb_homes):
            commande = "gnome-terminal --geometry 80x10 -- python3 " + path + "/home.py"
            os.system(commande)
    elif mode == 2:
        commandes = []
        print("\n\n--- Marché ---\n")
        prix_initial = input("    * Prix initial de l'énergie (en €/kWh) ? ==> ")
        gamma = input("    * Facteur d'atténuation du prix (0.99 par défaut) ? ==> ")
        print("    * Importance du facteur interne lié")
        modulation_historique = input("       aux transactions passées (0.001 par défaut) ? ==> ")
        modulation_strike = input("    * Importance du facteur externe lié à la grève (0.1 par défaut) ? ==> ")
        modulation_nuclear = input("    * Importance du facteur lié au nucléaire (1 par défaut) ? ==> ")
        parametres = prix_initial+" "+gamma+" "+modulation_historique+" "+modulation_strike+" "+modulation_nuclear
        commande = "gnome-terminal -- python3 " + path + "/market.py "+parametres
        commandes.append(commande)
        for i in range(0, nb_homes):
            print("\n\n--- Maison N°"+str(i)+" ---\n")
            type_home = input("    * Type 1 (donne), 2 (vend) ou 3 (mix) ? ==> ")
            prod_home = input("    * Production en kWh ? ==> ")
            conso_home = input("    * Consommation en kWh ? ==> ")
            parametres = type_home+" "+prod_home+" "+conso_home
            commande = "gnome-terminal -- python3 " + path + "/home.py "+parametres
            commandes.append(commande)

        for commande in commandes:
            os.system(commande)


    input("\n\nAppuyez sur entrée pour fermer la simulation\n\n\n")
    send_end_signals()
    input()



