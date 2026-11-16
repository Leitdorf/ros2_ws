import csv
import os
from collections import defaultdict
from statistics import mean, median

import matplotlib.pyplot as plt

STRATEGIES = [('levy', 'Lévy + carte'), ('bandes', 'Bandes'), ('frontiere', 'Frontière')]
PANNES = [('aucune', 'Sans panne'), ('turtle2', 'Panne de turtle2 à 5 s')]

temps = defaultdict(list)
ratees = defaultdict(int)
with open(os.path.expanduser('~/resultats_sar.csv')) as f:
    for ligne in csv.DictReader(f):
        cle = (ligne['strategie'], ligne['panne'], int(ligne['nb_robots']))
        temps[cle].append(float(ligne['temps_s']))
        if int(ligne['victimes']) < 5:
            ratees[cle] += 1

ns = sorted({n for (_, _, n) in temps})
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)

for ax, (panne, titre) in zip(axes, PANNES):
    print(f'===== {titre} =====')
    for (s, nom), decalage in zip(STRATEGIES, (-0.15, 0.0, 0.15)):
        xs, medianes, bas, haut = [], [], [], []
        for n in ns:
            t = temps.get((s, panne, n))
            if not t:
                continue
            m = median(t)
            xs.append(n + decalage)
            medianes.append(m)
            bas.append(m - min(t))
            haut.append(max(t) - m)
            texte = (f'{nom:13s} {n} robots : médiane {m:6.1f} s | moyenne {mean(t):6.1f} '
                     f'| min {min(t):5.1f} | max {max(t):5.1f} | {len(t)} missions')
            if ratees[(s, panne, n)]:
                texte += f' | {ratees[(s, panne, n)]} ratée(s)'
            print(texte)
        if xs:
            ax.errorbar(xs, medianes, yerr=[bas, haut], fmt='o-', capsize=4, label=nom)
    print()
    ax.set_title(titre)
    ax.set_xlabel('Nombre de robots')
    ax.set_xticks(ns)
    ax.grid(alpha=0.3)

axes[0].set_ylabel('Temps pour trouver les 5 victimes (s)')
axes[0].legend()

print('===== Surcoût de la panne (médiane avec / sans) =====')
for s, nom in STRATEGIES:
    ligne = f'{nom:13s}'
    for n in ns:
        a, p = temps.get((s, 'aucune', n)), temps.get((s, 'turtle2', n))
        ligne += f' | {n} robots : ' + (f'x {median(p) / median(a):.2f}' if a and p else '  -   ')
    print(ligne)

plt.tight_layout()
sortie = os.path.expanduser('~/ros2_ws/strategies.png')
plt.savefig(sortie, dpi=150)
print('\nGraphique enregistré :', sortie)