#!/bin/bash
# 3 tailles d'essaim x 2 modes x 2 graines = 12 missions
source ~/ros2_ws/install/setup.bash
for n in 2 4 8; do
  for p in true false; do
    for g in 3 4 5; do
      echo "=== $n robots, partage $p, graine $g ==="
      ros2 launch essaim_sar sar.launch.py n:=$n partage:=$p graine:=$g
    done
  done
done
echo "Terminé : résultats dans ~/resultats_sar.csv"