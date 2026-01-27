import time, socket, threading, sys
from multiprocessing import Lock
from multiprocessing.managers import BaseManager

HOST, MGR_PORT, SOCK_PORT, AUTH_KEY = '127.0.0.1', 50000, 6666, b'circleoflife'

class GameState:
    def __init__(self):
        self.grass = 100
        self.stats = {'preys': 0, 'active_preys': 0, 'preds': 0}
        self.drought = False 
        self.lock = Lock()

    def get_grass(self): return self.grass
    def get_stats(self): return self.stats
    def is_drought(self): return self.drought
    
    def eat_grass(self):
        with self.lock:
            if self.grass > 0:
                self.grass -= 1
                return True
            return False

    def grow_grass(self):
        with self.lock:
            if not self.drought and self.grass < 400: 
                self.grass += 8

    def set_drought(self, state):
        with self.lock:
            self.drought = state

    def update_stats(self, key, delta):
        with self.lock:
            self.stats[key] += delta
            if self.stats[key] < 0: self.stats[key] = 0

class SimulationManager(BaseManager): pass

class EnvProcess:
    def __init__(self):
        self.state = GameState()
        SimulationManager.register('get_state', callable=lambda: self.state)
        self.manager = SimulationManager(address=(HOST, MGR_PORT), authkey=AUTH_KEY)
        self.manager.start()
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((HOST, SOCK_PORT))
        self.sock.listen()

    def handle_socket(self, conn):
        with conn:
            while True:
                try:
                    data = conn.recv(1024).decode().split()
                    if not data: break
                    cmd, ptype = data[0], data[1]
                    
                    if cmd == "JOIN":
                        self.state.update_stats('preys' if ptype == "PREY" else 'preds', 1)
                        conn.sendall((1).to_bytes(4, 'big'))
                    elif cmd == "DIE":
                        self.state.update_stats('preys' if ptype == "PREY" else 'preds', -1)
                except: break

    def grass_loop(self):
        while True:
            time.sleep(0.5)
            self.state.grow_grass()

    def climate_cycle(self):
        while True:
            # 1. Saison des pluies (15 secondes)
            self.state.set_drought(False)
            time.sleep(15)
            
            # 2. Sécheresse (5 secondes)
            self.state.set_drought(True)
            time.sleep(5)

    def socket_listen(self):
        while True:
            try:
                c, _ = self.sock.accept()
                threading.Thread(target=self.handle_socket, args=(c,), daemon=True).start()
            except: break

    def start(self):
        threading.Thread(target=self.grass_loop, daemon=True).start()
        threading.Thread(target=self.climate_cycle, daemon=True).start() # Thread Météo
        threading.Thread(target=self.socket_listen, daemon=True).start()
        
        print("🌍 Environnement opérationnel.")
        
        # Boucle d'affichage
        while True:
            time.sleep(1) 
            s = self.state.get_stats()
            g = self.state.get_grass()
            drought = self.state.is_drought()
            weather_icon = "SÉCHERESSE" if drought
            
            print(f"[{weather_icon:<12}]  Herbe: {g:<3} |  Proies: {s['preys']:<3} (Act:{s['active_preys']}) |  Loups: {s['preds']:<3}")

if __name__ == "__main__":
    EnvProcess().start()
