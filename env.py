import time, socket, threading, sys, os, signal
from multiprocessing import Lock
from multiprocessing.managers import BaseManager
import sysv_ipc

HOST, MGR_PORT, SOCK_PORT, AUTH_KEY = '127.0.0.1', 50000, 6666, b'circleoflife'
MQ_KEY = 12345 

class GameState:
    def __init__(self):
        self.grass = 100
        self.stats = {'preys': 0, 'active_preys': 0, 'preds': 0}
        self.drought = False 
        self.lock = Lock()
    
    def grow_grass(self):
        with self.lock:
            if not self.drought and self.grass < 800: 
                self.grass += 15
    
    def set_drought(self, state):
        with self.lock: self.drought = state
    
    def is_drought(self): return self.drought
    def get_grass(self): return self.grass
    def get_stats(self): return self.stats
    
    def update_stats(self, key, delta):
        with self.lock:
            self.stats[key] = max(0, self.stats[key] + delta)

    def eat_grass(self):
        with self.lock:
            if self.grass > 0:
                self.grass -= 1
                return True
            return False

class SimulationManager(BaseManager): pass
global_state = GameState()

class EnvProcess:
    def __init__(self):
        SimulationManager.register('get_state', callable=lambda: global_state)
        self.manager = SimulationManager(address=(HOST, MGR_PORT), authkey=AUTH_KEY)
        try:
            self.manager.start()
        except OSError:
            print(f"Port {MGR_PORT} occupé.")
            sys.exit(1)

        self.state = self.manager.get_state()
        
        try:
            old_mq = sysv_ipc.MessageQueue(MQ_KEY)
            old_mq.remove()
        except: pass
        self.mq = sysv_ipc.MessageQueue(MQ_KEY, sysv_ipc.IPC_CREAT)

        signal.signal(signal.SIGUSR1, self.handle_drought)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((HOST, SOCK_PORT))
        self.sock.listen()
        
        self.active_prey_sockets = []
        self.lock_sockets = threading.Lock()

    def handle_drought(self, signum, frame):
        self.state.set_drought(not self.state.is_drought())

    def publish_to_mq(self):
        while True:
            s = self.state.get_stats()
            msg = f"{self.state.get_grass()}|{s['preys']}|{s['active_preys']}|{s['preds']}|{int(self.state.is_drought())}"
            try:
                self.mq.send(msg.encode(), type=1)
            except: break
            time.sleep(0.5)

    def handle_client(self, conn):
        client_type = None
        is_active_flag = False
        try:
            data = conn.recv(1024).decode().strip()
            if "JOIN PREY" in data:
                client_type = "PREY"
                self.state.update_stats('preys', 1)
            elif "JOIN PRED" in data:
                client_type = "PRED"
                self.state.update_stats('preds', 1)
            conn.sendall((1).to_bytes(4, 'big'))

            while True:
                data = conn.recv(1024)
                if not data: break
                msg = data.decode().strip()

                if msg == "STATE ACTIVE":
                    with self.lock_sockets:
                        if conn not in self.active_prey_sockets:
                            self.active_prey_sockets.append(conn)
                            is_active_flag = True
                            self.state.update_stats('active_preys', 1)
                elif msg == "STATE PASSIVE":
                    with self.lock_sockets:
                        if conn in self.active_prey_sockets:
                            self.active_prey_sockets.remove(conn)
                            is_active_flag = False
                            self.state.update_stats('active_preys', -1)
                elif msg == "ACTION HUNT":
                    with self.lock_sockets:
                        if self.active_prey_sockets:
                            victim = self.active_prey_sockets.pop(0)
                            try: 
                                victim.sendall(b"DEAD")
                                conn.sendall(b"EAT_OK")
                            except: conn.sendall(b"EAT_NONE")
                        else:
                            conn.sendall(b"EAT_NONE")
                elif msg.startswith("DIE"): break
        finally:
            with self.lock_sockets:
                if client_type == "PREY":
                    self.state.update_stats('preys', -1)
                    if is_active_flag: self.state.update_stats('active_preys', -1)
                    if conn in self.active_prey_sockets: self.active_prey_sockets.remove(conn)
                elif client_type == "PRED":
                    self.state.update_stats('preds', -1)
            conn.close()

    def start(self):
        threading.Thread(target=self.publish_to_mq, daemon=True).start()
        threading.Thread(target=lambda: [time.sleep(0.5) or self.state.grow_grass() for _ in iter(int, 1)], daemon=True).start()
        print("Simulation lancée...")
        try:
            while True:
                c, _ = self.sock.accept()
                threading.Thread(target=self.handle_client, args=(c,), daemon=True).start()
        except KeyboardInterrupt: pass

if __name__ == "__main__":
    EnvProcess().start()