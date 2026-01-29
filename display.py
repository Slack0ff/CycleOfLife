import time, sys, os, subprocess, signal
import sysv_ipc # Message Queue

MQ_KEY = 12345

def main():
    # 1. Demande utilisateur
    try:
        n_preys = int(input("Nombre de proies initiales : "))
        n_preds = int(input("Nombre de prédateurs initiaux : "))
    except: return

    # 2. Lancement de l'Env
    env_p = subprocess.Popen([sys.executable, "env20.py"])
    time.sleep(2) # Attendre que Env crée la MQ

    # 3. Connexion Display -> Message Queue
    try:
        mq = sysv_ipc.MessageQueue(MQ_KEY)
    except:
        print("Erreur: Impossible de se connecter à la MessageQueue.")
        os.kill(env_p.pid, 9)
        return
    
    # 4. Lancement des agents
    for _ in range(n_preys): subprocess.Popen([sys.executable, "prey.py"])
    for _ in range(n_preds): subprocess.Popen([sys.executable, "predator.py"])

    # Thread Climat
    def climate_controller(pid_env):
        while True:
            time.sleep(10)
            try: os.kill(pid_env, signal.SIGUSR1)
            except: break
            time.sleep(5)
            try: os.kill(pid_env, signal.SIGUSR1)
            except: break
            
    import threading
    threading.Thread(target=climate_controller, args=(env_p.pid,), daemon=True).start()

    # 5. Boucle d'affichage via Message Queue
    print("Démarrage de l'affichage via MQ...")
    try:
        while True:
            try:
                message, t = mq.receive(type=1) 
                data = message.decode().split('|')
                
                grass = int(data[0])
                preys = int(data[1])
                active = int(data[2])
                preds = int(data[3])
                is_drought = bool(int(data[4]))

                os.system('clear' if os.name == 'posix' else 'cls')
                print(f"--- SIMULATION ---")
                print(f"Météo: {'SÉCHERESSE !!!' if is_drought else 'Temps Normal'}")
                print(f"Herbe: {grass}")
                print(f"Proies: {preys} (Actives: {active})")
                print(f"Loups:  {preds}")
                print("------------------------------------------")
                print("(Appuyez sur Ctrl+C pour arrêter)")
            except sysv_ipc.Error:
                break          
    except KeyboardInterrupt:
        pass
    
if __name__ == "__main__":
    main()