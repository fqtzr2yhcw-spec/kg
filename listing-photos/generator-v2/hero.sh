#!/bin/bash
# usage: hero.sh <prod> <tag> <W> <H> <fov> <ox> <oy>   (W,H,ox,oy at final size; renders 2x)
set -e; P=$1; TAG=$2; W=$3; H=$4; FOV=$5; OX=$6; OY=$7
cd "$(dirname "$0")"
Q="cfg=/b2/rcfg_$P.json&w=$((W*2))&h=$((H*2))&fov=$FOV&ox=$((OX*2))&oy=$((OY*2))"
timeout 280 node render2.js "$Q" b2/r_${P}_${TAG}4k.png >/dev/null 2>&1
timeout 280 node render2.js "$Q&depth=1" b2/d_${P}_${TAG}4k.png >/dev/null 2>&1
cd b2 && python3 ../ds.py r_${P}_${TAG}4k r_${P}_${TAG} && python3 lib/composite2.py prod_$P.json r_${P}_${TAG}.png r_${P}_${TAG}.json hero_${P}_${TAG}.png 0.5
