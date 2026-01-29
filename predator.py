import time, socket, sys, subprocess, os
from multiprocessing.managers import BaseManager

# Configuration réseau
HOST, MGR_PORT, SOCK_PORT, AUTH_KEY = '127.0.0.1', 50000, 6666, b'circleoflife'

# Paramètres de simulation (Équilibrés pour la survie)
TICK = 0.5
DECAY = 0.8 # Vitesse de perte d'énergie
H_THRESHOLD = 60 
R_THRESHOLD = 90 # Seuil d'énergie déclenchant la reproduction

class SimulationManager(BaseManager): pass

class PredatorProcess:
    def __init__(self):
        self.energy = 80
        
        # 1. Connexion au Gestionnaire de Mémoire Partagée (pour lire l'état global si besoin)
        SimulationManager.register('get_state')
        self.mgr = SimulationManager(address=(HOST, MGR_PORT), authkey=AUTH_KEY)
        
        try:
            self.mgr.connect()
            self.shared_state = self.mgr.get_state()
            
            # 2. Connexion au Socket (pour les actions critiques : Chasser, Mourir)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, SOCK_PORT))
            self.sock.sendall(b"JOIN PRED")
            self.sock.recv(4) # Attente de l'accusé de réception (ID)
        except Exception:
            # Si l'environnement n'est pas dispo, on termine immédiatement
            os.kill(os.getpid(), 9)

    def run(self):
        try:
            while self.energy > 0:
                time.sleep(TICK)
                self.energy -= DECAY

                # --- COMPORTEMENT : CHASSE ---
                # Si l'énergie est basse, on envoie une requête de chasse à l'Env
                if self.energy < H_THRESHOLD:
                    try:
                        self.sock.sendall(b"ACTION HUNT")
                        
                        # On attend la réponse de l'Env pour savoir si on a mangé
                        self.sock.setblocking(True)
                        rep = self.sock.recv(1024)
                        
                        if b"EAT_OK" in rep:
                            self.energy += 40 # Gain d'énergie en cas de succès
                            
                        self.sock.setblocking(False)
                    except: pass

                # --- COMPORTEMENT : REPRODUCTION ---
                # Si l'énergie est suffisante, on crée un nouveau processus
                if self.energy > R_THRESHOLD:
                    self.energy -= 50
                    subprocess.Popen([sys.executable, "predator.py"])

                # Plafond d'énergie
                if self.energy > 100:
                    self.energy = 100

            # --- FIN DE VIE ---
            self.die_starvation()
            
        except KeyboardInterrupt:
            self.die_starvation()

    def die_starvation(self):
        """Notifie l'environnement de la mort et ferme les ressources."""
        try:
            self.sock.sendall(b"DIE PRED")
            self.sock.close()
        except: pass
        os.kill(os.getpid(), 9)

if __name__ == "__main__":
    PredatorProcess().run()
