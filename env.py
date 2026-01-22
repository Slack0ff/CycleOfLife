import socket
import time
import threading

from multiprocessing import Value, Semaphore


HOST = "localhost"
PORT = 6666

GRASS_GROWTH = 2
GRASS_MAX = 200


class EnvProcess:
    """
    Processus environnement central
    """

    def __init__(self):
        self.running = True
        self.drought = False

        # Compteurs d'ID uniques
        self.next_prey_id = 1
        self.next_predator_id = 1

        # Socket serveur
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((HOST, PORT))
        self.server.listen()

        print("[ENV] Environnement démarré")

    # ========================
    # GESTION DES CLIENTS
    # ========================
    def handle_client(self, conn):
        """
        Gère un client prey ou predator
        """
        with conn:
            while self.running:
                try:
                    msg = conn.recv(1024)
                    if not msg:
                        break

                    msg = msg.decode()

                    # ---------- PREY ----------
                    if msg == "PREY_JOIN":
                        sem_preys.acquire()

                        prey_id = self.next_prey_id
                        self.next_prey_id += 1

                        preys_total.value += 1
                        preys_active.value += 1

                        sem_preys.release()

                        # Envoi ID
                        conn.sendall(prey_id.to_bytes(4, "big"))

                        print(f"[ENV] Proie {prey_id} connectée")

                    # ---------- PREDATOR ----------
                    elif msg == "PREDATOR_JOIN":
                        sem_predators.acquire()

                        predator_id = self.next_predator_id
                        self.next_predator_id += 1

                        predators_total.value += 1

                        sem_predators.release()

                        # Envoi ID
                        conn.sendall(predator_id.to_bytes(4, "big"))

                        print(f"[ENV] Prédateur {predator_id} connecté")

                    elif msg == "PREDATOR_DIE":
                        sem_predators.acquire()
                        predators_total.value -= 1
                        sem_predators.release()

                        print("[ENV] Prédateur mort")
                        

                    elif msg == "PREY_DIE":
                        sem_preys.acquire()
                        preys_total.value -= 1
                        preys_active.value -= 1

                        sem_preys.release()
                        

                        print("[ENV] Proie morte")
                        break

                except ConnectionResetError:
                    break

    # ========================
    # CROISSANCE DE L'HERBE
    # ========================
    def grass_loop(self):
        """
        Fait pousser l'herbe sauf en sécheresse
        """
        while self.running:
            time.sleep(2)

            if not self.drought:
                sem_grass.acquire()

                if grass.value < GRASS_MAX:
                    grass.value += GRASS_GROWTH

                sem_grass.release()

    # ========================
    # GESTION SÉCHERESSE
    # ========================
    def drought_loop(self):
        """
        Déclenche une sécheresse périodique, une secheresse toutes les  20 secondes et pendant 10 secondes
        """
        while self.running:
            time.sleep(20)
            self.drought = True
            print("[ENV] Sécheresse")

            time.sleep(10)
            self.drought = False
            print("[ENV] Fin sécheresse")

    # ========================
    # AFFICHAGE ÉTAT GLOBAL
    # ========================
    def display_loop(self):
        """
        Affiche l'état global
        """
        while self.running:
            time.sleep(5)
            print(
                f"[ENV]  Herbe={grass.value} | "
                f" Proies={preys_total.value} (actives={preys_active.value}) | "
                f"Prédateurs={predators_total.value} | "
                f"Sécheresse={self.drought}"
            )

    # ========================
    # LANCEMENT
    # ========================
    def start(self):
        # Threads internes
        threading.Thread(target=self.grass_loop, daemon=True).start()
        threading.Thread(target=self.drought_loop, daemon=True).start()
        threading.Thread(target=self.display_loop, daemon=True).start()

        # Boucle serveur
        while self.running:
            conn, _ = self.server.accept()
            threading.Thread(
                target=self.handle_client,
                args=(conn,),
                daemon=True
            ).start()


# ========================
# POINT D'ENTRÉE
# ========================
if __name__ == "__main__":
    # Ressources partagées
    grass = Value('i', 100)

    preys_total = Value('i', 0)
    preys_active = Value('i', 0)

    predators_total = Value('i', 0)

# Sémaphores
    sem_grass = Semaphore(1)
    sem_preys = Semaphore(1)
    sem_predators = Semaphore(1)
    try:
        EnvProcess().start()
    except KeyboardInterrupt:
        print("\n[ENV] Arrêt de l'environnement")
