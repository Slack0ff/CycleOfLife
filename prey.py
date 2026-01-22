import sys
import time
import random
import struct
import socket
from multiprocessing import Process, Value, Lock
#Paramètres de base (à modifier hehe)
H_THRESHOLD = 70
R_THRESHOLD = 90
MAX_ENERGY = 100
DECAY_RATE = 2
TICK_RATE = 0.5

# On importe les ressources partagées créées par Env


class Prey(Process) :
    def __init__(self, shared_grass_count, grass_lock, env_host='localhost', env_port=5000, start_energy=50):
        super().__init__()
        self.energy = start_energy
        self.shared_grass = shared_grass_count
        self.grass_lock = grass_lock
        self.env_address = (env_host, env_port)
        self.id = None
        self.alive = True
       
       #=====================Connexion à ENV===================
        self.sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect_to_env()

    def connect_to_env(self):
        try:
            self.sock.connect(self.env_address)
            self.sock.sendall(b"PREY_JOIN")

            # Réception ID (4 octets)
            data = self.sock.recv(4)
            self.id = int.from_bytes(data, "big")

            print(f"[Prey {self.id}] connecté | énergie = {self.energy}")

        except ConnectionRefusedError:
            print("Impossible de contacter Env.")
            sys.exit(1)

           
    def check_state(self):
        if self.energy< H_THRESHOLD:
            return "ACTIVE"
        return "PASSIVE"
    def eat(self):
        with self.grass_lock:
            if self.shared_grass.value > 0 :
                self.shared_grass.value-=1
               
                gain = random.randint(10,30)
                self.energy = min(self.energy + gain, MAX_ENERGY)
                print(f"[Prey {self.id}] Rassasiement: Energie +{gain} (Total: {self.energy})")
            else:
                print(f"[Prey {self.id}] Pas d'herbe disponible...")
    def reproduce(self):
        print(f"[Prey {self.id}] Reproduction")
        energy_gift= self.energy / 2
        self.energy -=energy_gift
        child = Prey(self.shared_grass, self.grass_lock, start_energy=50)
        child.start()
       
    def run(self):
       
        while self.alive:
            self.energy-= DECAY_RATE
            if self.energy < 0:
                print(f"[Prey {self.id}] Morte de fatigue.")
                self.alive = False
                self.sock.sendall(b"PREY_DIE")
                break
           
        state = self.check_state()
        if state =="ACTIVE":
            self.eat()
        elif state == "PASSIVE":
            if self.energy> R_THRESHOLD:
                self.reproduce()
        time.sleep(TICK_RATE)
  