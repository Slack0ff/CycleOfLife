import socket
import threading
import time
import sys
import subprocess
from multiprocessing import Value, Semaphore

# Configuration
HOST, PORT = "localhost", 6666

class Env:
    def __init__(self):
        # Ressources partagées
        self.grass = Value('i', 100)
        self.prey_tot = Value('i', 0)   # Total proies
        self.prey_act = Value('i', 0)   # Proies actives (vulnérables)
        self.predator_tot = Value('i', 0)  # Total prédateurs
        
        # Sémaphore pour protéger les accès concurrents aux variables
        self.sem = Semaphore(1)
        
        self.next_id = 1
        self.running = True

    def spawn_initial_population(self):
        """Lance les processus initiaux via subprocess"""
        print("[ENV] Lancement de la population initiale...")
        # Lancer 10 Proies
        for _ in range(10):
            subprocess.Popen([sys.executable, "prey.py"])
        # Lancer 2 Prédateurs
        for _ in range(2):
            subprocess.Popen([sys.executable, "predator.py"])

    def handle_client(self, conn):
        """Gère un client (Proie ou Prédateur)"""
        with conn:
            while self.running:
                try:
                    data = conn.recv(1024)
                    if not data: break
                    msg = data.decode()

                    with self.sem:
                        if msg == "PREY_JOIN":
                            self.prey_tot.value += 1
                            reply = self.next_id.to_bytes(4, "big")
                            self.next_id += 1
                            conn.sendall(reply)
                        
                        elif msg == "PREDATOR_JOIN":
                            self.predator_tot.value += 1
                            reply = self.next_id.to_bytes(4, "big")
                            self.next_id += 1
                            conn.sendall(reply)

                        elif msg == "EAT_GRASS":
                            if self.grass.value > 0:
                                self.grass.value -= 1
                                conn.sendall(b"OK")
                            else:
                                conn.sendall(b"EMPTY")

                        elif msg == "GET_PREY":
                            # Un prédateur chasse
                            if self.prey_act.value > 0:
                                # On décrémente ici pour simuler la mort statistique
                                self.prey_act.value -= 1
                                self.prey_tot.value -= 1
                                conn.sendall(b"HUNTED")
                            else:
                                conn.sendall(b"NONE")

                        elif msg == "SET_ACTIVE": 
                            self.prey_act.value += 1
                        elif msg == "SET_PASSIVE": 
                            # On vérifie > 0 pour éviter des négatifs si synchronisation imparfaite
                            if self.prey_act.value > 0: self.prey_act.value -= 1
                        
                        elif msg == "PREY_DIE": 
                            if self.prey_tot.value > 0: self.prey_tot.value -= 1
                        elif msg == "PRED_DIE": 
                            if self.predator_tot.value > 0: self.predator_tot.value -= 1

                except ConnectionResetError:
                    break
                except Exception:
                    break

    def grass_loop(self):
        """Fait pousser l'herbe régulièrement"""
        while self.running:
            time.sleep(0.5) # Pousse plus vite pour soutenir la pop
            with self.sem:
                if self.grass.value < 200: self.grass.value += 2

    def display(self):
        """Affiche l'état de la simulation"""
        while self.running:
            time.sleep(0.5)
            # Affichage dynamique avec \r pour écraser la ligne précédente
            print(f"\r[SIMULATION] Herbe: {self.grass.value:3d} | Proies: {self.prey_tot.value:2d} (Vulnérables: {self.prey_act.value:2d}) | Prédateurs: {self.predator_tot.value:2d}   ", end="", flush=True)

    def start(self):
        # Lancer les threads de gestion
        threading.Thread(target=self.grass_loop, daemon=True).start()
        threading.Thread(target=self.display, daemon=True).start()
        
        # Préparer le serveur
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Permet de réutiliser le port immédiatement si on relance
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        
        # Démarrer la population (Maintenant que le serveur écoute, ou presque)
        # On lance la pop dans un thread à part ou juste après le bind pour éviter de bloquer
        self.spawn_initial_population()

        print("\n[ENV] Serveur démarré. CTRL+C pour quitter.")
        
        try:
            while self.running:
                c, _ = server.accept()
                threading.Thread(target=self.handle_client, args=(c,), daemon=True).start()
        except KeyboardInterrupt:
            print("\n[ENV] Arrêt de la simulation...")
            self.running = False

if __name__ == "__main__":
    Env().start()
