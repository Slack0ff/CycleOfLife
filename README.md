# Projet Circle of Life
 ---
Fait par Oaissa Adam et Malamba Ruth 



## Présentation 
Le projet consiste à concevoir et implémenter une simulation multiprocessus en Python d’un petit écosystème composé d’herbivores, de carnivores et d’une ressource végétale (l’herbe). Chaque type d’individu est simulé par un processus distinct (env, prey, predator, display) : l’env centralise l’état partagé, les prey et predator incarnent les comportements (énergie, chasse, reproduction) et le display permet d’observer et de piloter la simulation en temps réel. L’objectif est d’étudier comment les interactions locales (consommation, prédation, reproduction) et les contraintes environnementales (croissance de l’herbe, épisodes de sécheresse) façonnent l’évolution des populations.

### Principe
Considérons un écosystème simple composé de prédateurs carnivores, de proies herbivores et d'herbe.

Les prédateurs et les proies possèdent un indicateur de vitalité, appelé énergie, qui diminue régulièrement au cours de la simulation,
indépendamment de l'état de l'individu. À tout instant, un individu se trouve dans l'un des deux états suivants : actif ou passif.
- Les prédateurs et les proies actifs se nourrissent respectivement de proies et d'herbe,si leur énergie est inférieure à un seuil donné H. 
- Seules les proies actives peuvent être la proie d'un prédateur. 

Un individu change d'état de manière déterministe (c'est-à-dire actif dès que son énergie est inférieure à H, passif dès que son énergie est supérieure à H). Se nourrir diminue les populations de proies et d'herbe. De plus, un individu se reproduit si son énergie est supérieure à un seuil donné R, augmentant ainsi sa population. Un individu meurt si son
énergie devient négative. En dehors des épisodes de sécheresse intermittents, l'herbe pousse régulièrement.

## Lancement du programme
### Prérequis 
- Langage : Python 
- Bibliothèques : multiprocessing, socket, sysv_ipc (pour la file de messages).
- Système : Environnement Linux/Unix recommandé pour la gestion optimale des signaux et de l'IPC.

### Exécution
1.	Lancement : Exécuter le script principal python display.py.
2.	Configuration : L'utilisateur est invité à saisir le nombre initial de proies et de prédateurs.
3.	Lecture des Logs : La console affiche en temps réel :
o	L'état de la météo (PLUIE / SÉCHERESSE).
o	Le compteur d'herbe.
o	Le ratio Proies Totales / Proies Actives (vulnérables).
o	Le nombre de prédateurs
4.	Arrêt : Une interruption clavier (Ctrl+C) déclenche une procédure de fermeture propre qui tue les processus enfants et libère la mémoire partagée.
