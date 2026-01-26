import time, socket, sys, subprocess, random, os, signal
from multiprocessing.managers import BaseManager

HOST, MGR_PORT, SOCK_PORT, AUTH_KEY = '127.0.0.1', 50000, 6666, b'circleoflife'

TICK = 0.5
DECAY = 3

class SimulationManager(BaseManager): pass

class PredatorProcess:
    def __init__(self):
        self.energy = 80
        SimulationManager.register('get_state')
        self.mgr = SimulationManager(address=(HOST, MGR_PORT), authkey=AUTH_KEY)
        try:
            self.mgr.connect()
            self.shared_state = self.mgr.get_state()
            
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, SOCK_PORT))
            self.sock.sendall(b"JOIN PRED")
            self.id = int.from_bytes(self.sock.recv(4), 'big')
        except: 
            os.kill(os.getpid(), signal.SIGTERM)

    def run(self):
        while self.energy > 0:
            time.sleep(TICK)
            self.energy -= DECAY

            if self.energy < 70:
                stats = self.shared_state.get_stats()
                if stats['active_preys'] > 0:
                    self.shared_state.update_stats('preys', -1)
                    self.shared_state.update_stats('active_preys', -1)
                    self.energy += 50
                    if self.energy > 100: self.energy = 100
                    try: self.sock.sendall(b"ACTION HUNT")
                    except: pass

            if self.energy > 90 and random.random() < 0.1:
                self.energy -= 60
                self.sock.sendall(b"ACTION REPRO")
                subprocess.Popen([sys.executable, "predator.py"])

        self.die()

    def die(self):
        try:
            self.sock.sendall(b"DIE PRED")
            self.sock.close()
        except: pass
        
        # MORT PAR SIGNAL SYSTÈME
        os.kill(os.getpid(), signal.SIGTERM)

if __name__ == "__main__":
    PredatorProcess().run()