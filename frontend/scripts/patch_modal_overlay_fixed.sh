#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 frontend/scripts/patch_modal_overlay_fixed.py
