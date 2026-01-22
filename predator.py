import sys
import time
import random
import struct
import socket
import subprocess
from multiprocessing import shared_memory, Semaphore, Process




#==========================Config global=============
H_THRESHOLD = 50     # Seuil faim
R_THRESHOLD = 90     # Seuil reproduction
DECAY_RATE = 2       # Perte d'énergie par tick
ENERGY_MAX = 100
ENERGY_INIT = 60
HOST = "localhost"
PORT = 6666          # Port de Env

class PredatorProcess(Process):
    """
   Processus representant un predateur
    """ 
    def __init__(self):
        super().__init__()
        self.energy=ENERGY_INIT
        self.alive=True
        self.id =None
        

        #=====================Connexion à ENV===================
        self.sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect_to_env()
        



    def connect_to_env(self):
        """
        Crée une connexion socket vers le processus env
        """

       
        try:
            self.sock.connect((HOST, PORT))
            self.sock.sendall(b"PREDATOR_JOIN")

            # Réception ID (4 octets)
            data = self.sock.recv(4)
            self.id = int.from_bytes(data, "big")

            print(f"[Predator {self.id}] connecté | énergie = {self.energy}")

        except ConnectionRefusedError:
            print("Impossible de contacter Env.")
            sys.exit(1)

    def hunt(self):
        """
        Tente de manger une proie actie
        L'accès est protégé par sémaphore
        """
        sem_preys.acquire()
        if preys_active.value > 0: 
            preys_active.value -= 1
            preys_total.value -=1

            gain = random.randint(20,35)
            self.energy =min(self.energy + gain, ENERGY_MAX) #pour pas depasser 100

            print(f"[Predator {self.id}] mange une proie (+{gain}) -> {self.energy}")
            success=True

        else :
            print(f"[Predator {self.id} aucune proie active à consommer]")
            success=False
        
        sem_preys.release()
        return success
        

    def reproduce(self):
        """
        Reproduction avec délai imposé 
        """
        print(f"[Predator {self.id}] reproduction")
        self.energy -=40

        time.sleep(5) #on attend 5 secondes avant de lancer le nouveau processus

        # Lancement d'un nouveau processus predator
        subprocess.Popen([sys.executable,__file__])

    def die(self):
        """
        Mort propre
        """
        print(f"[Predator {self.id}] mort")
        self.alive= False
        self.sock.sendall(b"PREDATOR_DIE")

    # === BOUCLE DE VIE=========
    def run(self):
        """
        Boucle de vie du prédateur
        """
        print(f"[Predator {self.id}] énergie initiale {self.energy}")

        while self.alive:
            time.sleep(1)

            #perte naturelle d'énergie
            self.energy -=DECAY_RATE

            #Mort
            if self.energy<=0:
                self.die()
                break

            #Tant que faim alors chasse (hunt)
            while self.energy< H_THRESHOLD:
                if not self.hunt():
                    break
                time.sleep(1)

            if self.energy>= R_THRESHOLD:
                self.reproduce()
        self.cleanup()

    def cleanup(self):
        self.sock.close()
        print(f"[Predator {self.id}] terminé propremenent")


#============================================
#POINT D ENTREE
#============================================
if __name__=="__main__":
    try:
        PredatorProcess().run()
    except KeyboardInterrupt:
        print("Arrêt manuel predator")
