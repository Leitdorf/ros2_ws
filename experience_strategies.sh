#!/bin/bash
# 3 stratégies x 3 tailles x 2 cas de panne x 5 graines = 90 missions
source ~/ros2_ws/install/setup.bash
for g in 1 2 3 4 5; do
  for n in 2 4 8; do
    for p in aucune turtle2; do
      for s in levy bandes frontiere; do
        echo "=== graine $g, $n robots, panne $p, $s ==="
        ros2 launch essaim_sar sar.launch.py n:=$n strategie:=$s panne:=$p t_panne:=5 graine:=$g
      done
    done
  done
done
echo "Terminé : résultats dans ~/resultats_sar.csv"