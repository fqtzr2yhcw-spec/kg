#!/bin/bash
# SessionStart hook: install the 3D-modeling toolchain (OpenSCAD, Blender, and
# the Python mesh libraries) so Claude Code on the web sessions can build and
# export printable 3D models. Idempotent and non-interactive.
set -euo pipefail

# Only needed in remote (Claude Code on the web) containers; skip locally.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

log=/tmp/3d-toolchain-setup.log
: > "$log"

# System CAD/mesh apps (both run headless in this environment).
# Idempotent: skip the apt work if they're already present (cached containers).
if ! command -v openscad >/dev/null 2>&1 \
   || ! command -v blender  >/dev/null 2>&1 \
   || ! command -v xvfb-run >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -o Acquire::Retries=2 >>"$log" 2>&1 || true
  apt-get install -y openscad blender xvfb   >>"$log" 2>&1
fi

# Python mesh/CAD libraries (the pipeline that generates the STL sections).
if ! python3 -c "import trimesh, manifold3d, scipy, numpy, matplotlib" >/dev/null 2>&1; then
  python3 -m pip install --user --break-system-packages --quiet \
    trimesh manifold3d scipy numpy matplotlib >>"$log" 2>&1
fi

echo "3D toolchain ready: $(openscad --version 2>&1 | head -1) | $(blender --version 2>&1 | head -1)"
