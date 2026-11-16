#!/bin/bash
# 4 robots, sans panne / avec panne de turtle2 à 20 s, 5 graines = 10 missions
source ~/ros2_ws/install/setup.bash
for p in aucune turtle2; do
  for g in 1 2 3 4 5; do
    echo "=== panne $p, graine $g ==="
    ros2 launch essaim_sar sar.launch.py n:=4 panne:=$p graine:=$g
  done
done
echo "Terminé : résultats dans ~/resultats_sar.csv"