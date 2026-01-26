import time
import socket
import threading
import sys
import subprocess
from multiprocessing import Lock
from multiprocessing.managers import BaseManager

# ================= CONFIGURATION =================
HOST = '127.0.0.1'
MGR_PORT = 50000
SOCK_PORT = 6666
AUTH_KEY = b'circleoflife'

class GameState:
    def __init__(self):
        self.grass = 100
        self.stats = {'preys': 0, 'active_preys': 0, 'preds': 0}
        self.logs = [] 
        self.lock = Lock()

    def get_grass(self): return self.grass
    def get_stats(self): return self.stats
    def get_logs(self): return self.logs

    def add_log(self, msg):
        with self.lock:
            timestamp = time.strftime('%H:%M:%S')
            self.logs.append(f"[{timestamp}] {msg}")
            if len(self.logs) > 10: self.logs.pop(0)

    def eat_grass(self):
        with self.lock:
            if self.grass > 0:
                self.grass -= 1
                return True
            return False

    def grow_grass(self, amount):
        with self.lock:
            if self.grass < 500: self.grass += amount

    def update_stats(self, key, delta):
        with self.lock:
            self.stats[key] += delta
            if self.stats[key] < 0: self.stats[key] = 0

class SimulationManager(BaseManager): pass

class EnvProcess:
    def __init__(self):
        self.running = True
        self.next_id = 1
        
        # Shared Memory
        self.state = GameState()
        SimulationManager.register('get_state', callable=lambda: self.state)
        self.manager = SimulationManager(address=(HOST, MGR_PORT), authkey=AUTH_KEY)
        self.manager.start()

        # Socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((HOST, SOCK_PORT))
        self.sock.listen()

    def handle_client_socket(self, conn):
        client_id, client_type = 0, "?"
        with conn:
            while self.running:
                try:
                    data = conn.recv(1024).decode().strip()
                    if not data: break
                    
                    parts = data.split()
                    cmd = parts[0]

                    if cmd == "JOIN":
                        client_type = parts[1]
                        client_id = self.next_id
                        self.next_id += 1
                        
                        key = 'preys' if client_type == "PREY" else 'preds'
                        self.state.update_stats(key, 1)
                        self.state.add_log(f"✨ NAISSANCE: {client_type} #{client_id}")
                        conn.sendall(client_id.to_bytes(4, 'big'))
                    
                    elif cmd == "ACTION":
                        act = parts[1]
                        if act == "REPRO": 
                            self.state.add_log(f"REPRO: {client_type} #{client_id}")
                        elif act == "HUNT": 
                            self.state.add_log(f" CHASSE: Loup #{client_id} a mangé")

                    elif cmd == "DIE":
                        key = 'preys' if client_type == "PREY" else 'preds'
                        self.state.update_stats(key, -1)
                        self.state.add_log(f" MORT: {client_type} #{client_id}")
                        break
                except: break

    def display_loop(self):
        while self.running:
            time.sleep(0.5)
            s = self.state.get_stats()
            g = self.state.get_grass()
            logs = self.state.get_logs()
            
            # Nettoyage console (ANSI)
            print("\033[H\033[2J", end="") 
            print("╔══════════════════════════════════════════════════════╗")
            print(f"║  HERBE: {g:<4} |  PROIES: {s['preys']:<3} (Vuln: {s['active_preys']}) | LOUPS: {s['preds']:<3} ║")
            print("╚══════════════════════════════════════════════════════╝")
            
    def start(self):
        threading.Thread(target=self.display_loop, daemon=True).start()
        
        def grass_timer():
            while self.running:
                time.sleep(1)
                self.state.grow_grass(10)
        threading.Thread(target=grass_timer, daemon=True).start()

        print("Lancement de la simulation...")
        for _ in range(8): subprocess.Popen([sys.executable, "prey2.py"])
        for _ in range(2): subprocess.Popen([sys.executable, "predator2.py"])

        try:
            while self.running:
                conn, _ = self.sock.accept()
                threading.Thread(target=self.handle_client_socket, args=(conn,), daemon=True).start()
        except KeyboardInterrupt:
            self.running = False
            self.manager.shutdown()

if __name__ == "__main__":
    EnvProcess().start()