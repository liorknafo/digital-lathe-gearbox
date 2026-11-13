#!/bin/sh
# Compiles the firmware motion core + UI to WebAssembly for the browser simulator.
# Needs an LLVM clang with the wasm32 target and wasm-ld (brew install llvm lld).
set -e
cd "$(dirname "$0")"
CLANG="${CLANG:-/opt/homebrew/opt/llvm/bin/clang++}"
CORE=../firmware/lib/els_core/src

"$CLANG" --target=wasm32 -std=c++17 -O2 -ffreestanding -nostdlib -fno-exceptions -fno-rtti \
  -fvisibility=hidden -I"$CORE" \
  -Wl,--no-entry -Wl,--export-dynamic -Wl,--allow-undefined -Wl,-z,stack-size=262144 \
  -o web/els.wasm \
  wasm_api.cpp "$CORE/els.cpp" "$CORE/follower.cpp" "$CORE/pitch.cpp" "$CORE/ui.cpp"

# Also embed it as base64 so index.html works straight from disk (file:// can't fetch).
printf 'window.ELS_WASM_B64 = "%s";\n' "$(base64 < web/els.wasm | tr -d '\n')" > web/els_wasm.js

echo "built sim/web/els.wasm ($(wc -c < web/els.wasm) bytes)"
