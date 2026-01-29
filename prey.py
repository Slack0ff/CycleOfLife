import time, socket, sys, subprocess, os
from multiprocessing.managers import BaseManager

HOST, MGR_PORT, SOCK_PORT, AUTH_KEY = '127.0.0.1', 50000, 6666, b'circleoflife'

class PreyProcess:
    def __init__(self):
        self.energy = 50
        self.active = False
        BaseManager.register('get_state')
        self.mgr = BaseManager(address=(HOST, MGR_PORT), authkey=AUTH_KEY)
        self.mgr.connect()
        self.state = self.mgr.get_state()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, SOCK_PORT))
        self.sock.sendall(b"JOIN PREY")
        self.sock.recv(4)
        self.sock.setblocking(False)

    def run(self):
        while self.energy > 0:
            time.sleep(0.5)
            self.energy -= 1
            
            # Vérifier si l'Env nous a tué
            try:
                if self.sock.recv(1024) == b"DEAD": 
                    os.kill(os.getpid(), 9) # Suicide immédiat par PID
            except: pass

            # Logique faim / état
            if self.energy < 60 and not self.active:
                self.active = True
                self.sock.sendall(b"STATE ACTIVE")
            elif self.energy > 85 and self.active:
                self.active = False
                self.sock.sendall(b"STATE PASSIVE")

            if self.active and self.state.eat_grass():
                self.energy += 20
            
            # Reproduction
            if self.energy > 90 :
                self.energy -= 50
                subprocess.Popen([sys.executable, "prey.py"])
        
        self.sock.sendall(b"DIE")
        os.kill(os.getpid(), 9)

if __name__ == "__main__":
    PreyProcess().run()