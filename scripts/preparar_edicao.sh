#!/usr/bin/env bash
# Prepara o video-use e o Hyperframes em ferramentas/ (fora do git).
# Rode uma vez por sessao nova: bash scripts/preparar_edicao.sh
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p ferramentas
[ -d ferramentas/video-use ] || git clone --depth 1 https://github.com/browser-use/video-use ferramentas/video-use
[ -d ferramentas/hyperframes ] || git clone --depth 1 https://github.com/heygen-com/hyperframes ferramentas/hyperframes
pip install -q librosa matplotlib requests pillow numpy
npx --yes hyperframes --version >/dev/null
echo "export HYPERFRAMES_BROWSER_PATH=$(find /opt/pw-browsers -name chrome-headless-shell -type f 2>/dev/null | head -1)"
