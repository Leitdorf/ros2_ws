import csv
import os
from collections import defaultdict
from statistics import mean, median

temps = defaultdict(list)
with open(os.path.expanduser('~/resultats_sar.csv')) as f:
    for ligne in csv.DictReader(f):
        temps[ligne['panne']].append(float(ligne['temps_s']))

for panne in ['aucune', 'turtle2']:
    t = temps[panne]
    if t:
        print(f'panne {panne:8s} : moyenne {mean(t):6.1f} s | médiane {median(t):6.1f} s '
              f'| min {min(t):5.1f} | max {max(t):5.1f} | {len(t)} missions')