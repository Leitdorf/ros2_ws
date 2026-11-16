import csv
import os
from collections import defaultdict

import matplotlib.pyplot as plt

temps = defaultdict(list)
ratees = []
with open(os.path.expanduser('~/resultats_sar.csv')) as f:
    for ligne in csv.DictReader(f):
        cle = (ligne['partage'], int(ligne['nb_robots']))
        temps[cle].append(float(ligne['temps_s']))
        if int(ligne['victimes']) < 5:
            ratees.append(ligne)

courbes = [('True', 'carte partagée', -0.1), ('False', 'mémoire perso', 0.1)]
for partage, etiquette, decalage in courbes:
    ns = sorted(n for (p, n) in temps if p == partage)
    moyennes, bas, haut = [], [], []
    for n in ns:
        t = temps[(partage, n)]
        m = sum(t) / len(t)
        moyennes.append(m)
        bas.append(m - min(t))
        haut.append(max(t) - m)
        print(f'{etiquette:15s} {n} robots : moyenne {m:6.1f} s '
              f'(min {min(t):5.1f}, max {max(t):5.1f}, {len(t)} missions)')
    plt.errorbar([n + decalage for n in ns], moyennes, yerr=[bas, haut],
                 fmt='o-', capsize=4, label=etiquette)

if ratees:
    print(f'\nAttention : {len(ratees)} mission(s) sans les 5 victimes :')
    for l in ratees:
        print(f"  {l['nb_robots']} robots, partage {l['partage']}, graine {l['graine']} : "
              f"{l['victimes']}/5 en {l['temps_s']} s")

plt.xlabel('Nombre de robots')
plt.ylabel('Temps pour trouver les 5 victimes (s)')
plt.title('Essaim de sauvetage : moyenne, min et max sur 5 missions')
plt.xticks([2, 4, 8])
plt.grid(alpha=0.3)
plt.legend()
sortie = os.path.expanduser('~/ros2_ws/temps_vs_robots.png')
plt.savefig(sortie, dpi=150)
print('\nGraphique enregistré :', sortie)