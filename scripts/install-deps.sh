#!/usr/bin/env sh
# Instala ffmpeg y Deno si faltan: los usa la descarga de video de YouTube
# (ADR-0020). macOS via brew, Linux/WSL via apt, Windows nativo (Git Bash /
# MSYS) via winget o choco. Sin prompts propios; sudo/winget pueden pedir
# confirmación del sistema por su cuenta.
set -eu

warn() { printf '%s\n' "$1" >&2; }

os_is_macos() { [ "$(uname -s)" = "Darwin" ]; }

# Git Bash y MSYS reportan uname -s como MINGW64_NT-*/MSYS_NT-*; $OS lo pone
# Windows en cmd, PowerShell y Git Bash por igual.
os_is_windows() {
  case "$(uname -s 2>/dev/null || true)" in
    MINGW* | MSYS* | CYGWIN*) return 0 ;;
  esac
  [ "${OS:-}" = "Windows_NT" ]
}

install_ffmpeg() {
  command -v ffmpeg >/dev/null 2>&1 && return 0
  warn "Instalando ffmpeg…"
  if os_is_macos && command -v brew >/dev/null 2>&1; then
    brew install ffmpeg
  elif os_is_windows && command -v winget >/dev/null 2>&1; then
    winget install --id Gyan.FFmpeg -e --source winget \
      --accept-package-agreements --accept-source-agreements
  elif os_is_windows && command -v choco >/dev/null 2>&1; then
    choco install ffmpeg -y
  elif command -v apt >/dev/null 2>&1; then
    sudo apt-get update -qq && sudo apt-get install -y ffmpeg
  else
    warn "No se pudo instalar ffmpeg automáticamente (sin brew, winget, choco ni apt). Instalalo a mano: ver docs/troubleshooting.md."
    return 1
  fi
}

install_deno() {
  command -v deno >/dev/null 2>&1 && return 0
  warn "Instalando deno…"
  if os_is_macos && command -v brew >/dev/null 2>&1; then
    brew install deno
  elif os_is_windows && command -v winget >/dev/null 2>&1; then
    winget install --id DenoLand.Deno -e --source winget \
      --accept-package-agreements --accept-source-agreements
  elif os_is_windows && command -v choco >/dev/null 2>&1; then
    choco install deno -y
  else
    if ! command -v unzip >/dev/null 2>&1 && ! command -v 7z >/dev/null 2>&1; then
      warn "No se pudo instalar Deno: falta unzip o 7z para descomprimirlo. En Debian/Ubuntu/WSL: sudo apt-get install unzip. Después volvé a ejecutar ./dev.sh (ver docs/troubleshooting.md)."
      return 1
    fi
    curl -fsSL https://deno.land/install.sh | sh
  fi
}

status=0
install_ffmpeg || status=1
install_deno || status=1

if os_is_windows && [ "$status" -eq 0 ]; then
  warn "Si winget/choco acaban de instalar algo, puede hacer falta reabrir la terminal para que el PATH lo vea."
fi

exit "$status"
