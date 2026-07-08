#!/usr/bin/env bash
# Local build helper for Zarne (ZMK).
#
# Usage:
#   ./build.sh                 # build all 4 variants + copy to firmware/
#   ./build.sh oled_left       # build one target
#   ./build.sh nice_view_left  # nice!view variant
#   ./build.sh settings_reset  # build settings reset firmware
#   ./build.sh list            # show available targets
#
# Outputs land in build/<target>/zephyr/zmk.uf2
# Copied to firmware/<target>.uf2 after each build
#
# First-time setup (run once):
#   python3.10 -m venv .venv
#   . .venv/bin/activate
#   pip install -r requirements-build.txt
#   west init -l config && west update && west zephyr-export
#   pip install -r zephyr/scripts/requirements.txt
#   # Zephyr SDK 0.16.9 (arm-zephyr-eabi) installed at $HOME/zephyr-sdk-0.16.9
set -euo pipefail
cd "$(dirname "$0")"

# Toolchain env
export ZEPHYR_TOOLCHAIN_VARIANT="${ZEPHYR_TOOLCHAIN_VARIANT:-zephyr}"
export ZEPHYR_SDK_INSTALL_DIR="${ZEPHYR_SDK_INSTALL_DIR:-$HOME/zephyr-sdk-0.16.9}"

# Use the venv if present
[ -f .venv/bin/activate ] && . .venv/bin/activate

CONFIG="$PWD/config"
FIRMWARE_DIR="$PWD/firmware"

# target name -> shield string
declare -A SHIELDS=(
  [oled_left]="zarne_left zarne_oled nice_oled"
  [oled_right]="zarne_right zarne_oled nice_oled"
  [nice_view_left]="zarne_left nice_view_adapter nice_epaper"
  [nice_view_right]="zarne_right nice_view_adapter nice_epaper"
  [settings_reset]="settings_reset"
)

build_one() {
  local name="$1"
  local shield="${SHIELDS[$name]:-}"
  if [ -z "$shield" ]; then
    echo "Unknown target '$name'. Run './build.sh list'." >&2; exit 1
  fi
  echo ">>> Building $name  (shield: $shield)"
  west build -p -s zmk/app -b nice_nano_v2 -d "build/$name" -- \
    -DSHIELD="$shield" -DZMK_CONFIG="$CONFIG"
  mkdir -p "$FIRMWARE_DIR"
  cp "build/$name/zephyr/zmk.uf2" "$FIRMWARE_DIR/$name.uf2"
  echo ">>> $name -> firmware/$name.uf2"
}

case "${1:-all}" in
  list) printf '%s\n' "${!SHIELDS[@]}" | sort ;;
  all)
    build_one oled_left
    build_one oled_right
    build_one nice_view_left
    build_one nice_view_right
    ;;
  *) build_one "$1" ;;
esac
