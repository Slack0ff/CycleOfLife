# shared_resources.py
from multiprocessing import Value, Semaphore

# Ressources partagées
grass = Value('i', 100)

preys_total = Value('i', 0)
preys_active = Value('i', 0)

predators_total = Value('i', 0)

# Sémaphores
sem_grass = Semaphore(1)
sem_preys = Semaphore(1)
sem_predators = Semaphore(1)