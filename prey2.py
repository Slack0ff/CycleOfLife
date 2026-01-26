import time, socket, sys, subprocess, random, os, signal
from multiprocessing.managers import BaseManager

HOST, MGR_PORT, SOCK_PORT, AUTH_KEY = '127.0.0.1', 50000, 6666, b'circleoflife'

TICK = 0.5
DECAY = 2
EAT_GAIN = 30

class SimulationManager(BaseManager): pass

class PreyProcess:
    def __init__(self):
        self.energy = 70
        self.active = False
        
        SimulationManager.register('get_state')
        self.mgr = SimulationManager(address=(HOST, MGR_PORT), authkey=AUTH_KEY)
        try:
            self.mgr.connect()
            self.shared_state = self.mgr.get_state()
            
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, SOCK_PORT))
            self.sock.sendall(b"JOIN PREY")
            self.id = int.from_bytes(self.sock.recv(4), 'big')
        except: 
            # Si échec connexion, on se tue directement
            os.kill(os.getpid(), signal.SIGTERM)

    def run(self):
        while self.energy > 0:
            time.sleep(TICK)
            self.energy -= DECAY

            if self.energy < 60 and not self.active:
                self.active = True
                self.shared_state.update_stats('active_preys', 1)
            
            if self.active:
                if self.shared_state.eat_grass():
                    self.energy += EAT_GAIN
                    if self.energy >= 90:
                        self.active = False
                        self.shared_state.update_stats('active_preys', -1)
                        self.energy = 100

            if self.energy > 90 and random.random() < 0.2:
                self.energy -= 40
                self.sock.sendall(b"ACTION REPRO")
                subprocess.Popen([sys.executable, "prey.py"])

        self.die()

    def die(self):
        if self.active: self.shared_state.update_stats('active_preys', -1)
        try:
            self.sock.sendall(b"DIE PREY")
            self.sock.close()
        except: pass
        
        # MORT PAR SIGNAL SYSTÈME
        my_pid = os.getpid()
        # On envoie le signal SIGTERM (15) à soi-même
        os.kill(my_pid, signal.SIGTERM)

if __name__ == "__main__":
    PreyProcess().run()