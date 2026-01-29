import time, socket, sys, subprocess, os
from multiprocessing.managers import BaseManager

HOST, MGR_PORT, SOCK_PORT, AUTH_KEY = '127.0.0.1', 50000, 6666, b'circleoflife'

TICK = 0.5
DECAY = 1.5     
H_THRESHOLD = 70 # Seuil pour chasser
R_THRESHOLD = 90 # Seuil pour se reproduire

class SimulationManager(BaseManager): pass

class PredatorProcess:
    def __init__(self):
        self.energy = 80
        # Connexion au Manager pour voir les stats globales
        SimulationManager.register('get_state')
        self.mgr = SimulationManager(address=(HOST, MGR_PORT), authkey=AUTH_KEY)
        try:
            self.mgr.connect()
            self.shared_state = self.mgr.get_state()
            
            # Connexion Socket pour les actions (HUNT, DIE)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, SOCK_PORT))
            self.sock.sendall(b"JOIN PRED")
            # On reçoit l'ID (optionnel ici)
            self.sock.recv(4)
        except Exception as e:
            # Si l'env est fermé, on se tue par PID
            os.kill(os.getpid(), 9)

    def run(self):
        while self.energy > 0:
            time.sleep(TICK)
            self.energy -= DECAY

            # 1. LOGIQUE DE CHASSE
            if self.energy < H_THRESHOLD:
                # On demande à l'environnement de chasser une proie active
                    self.sock.sendall(b"ACTION HUNT")
                    # Ici on simule un gain d'énergie fixe si on a tenté de chasser
                    try:
                        self.sock.setblocking(True)
                        rep = self.sock.recv(1024)
                        if b"EAT_OK" in rep:
                            self.energy += 50
                        self.sock.setblocking(False)
                    except: pass

            # 2. REPRODUCTION
            if self.energy > R_THRESHOLD:
                self.energy -= 50
                # On lance un nouveau processus prédateur
                subprocess.Popen([sys.executable, "predator.py"])

            if self.energy > 100:
                self.energy = 100

        # 3. MORT PAR FAMINE
        self.die_starvation()

    def die_starvation(self):
        try:
            self.sock.sendall(b"DIE PRED")
            self.sock.close()
        except:
            pass
        # Kill final via PID 
        os.kill(os.getpid(), 9)

if __name__ == "__main__":
    PredatorProcess().run()