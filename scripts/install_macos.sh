#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: install_macos.sh --printer-ip <LAN-IP> [options]

Options:
  --printer-ip <address>  Printer LAN IP or trusted private hostname (required)
  --serial <serial>       Select one printer when Bambu Studio has multiple printers
  --config <path>         Override BambuStudio.conf location
  --printer-name <name>   Label shown in the overlay (default: Bambu printer)
  --dry-run               Validate arguments and show destinations without changing files
  -h, --help              Show this help
EOF
}

printer_ip=""
printer_serial=""
config_path=""
printer_name="Bambu printer"
dry_run=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --printer-ip) printer_ip="${2:-}"; shift 2 ;;
    --serial) printer_serial="${2:-}"; shift 2 ;;
    --config) config_path="${2:-}"; shift 2 ;;
    --printer-name) printer_name="${2:-}"; shift 2 ;;
    --dry-run) dry_run=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$printer_ip" ]]; then
  echo "--printer-ip is required" >&2
  exit 2
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "$script_dir/.." && pwd)"
install_dir="$HOME/Library/Application Support/BambuLiveOverlay"
output_dir="$install_dir/output"
log_dir="$HOME/Library/Logs/BambuLiveOverlay"
launch_agents="$HOME/Library/LaunchAgents"
label="com.bambu-live-overlay.agent"
plist_path="$launch_agents/$label.plist"

if [[ "$dry_run" -eq 1 ]]; then
  printf 'Install directory: %s\n' "$install_dir"
  printf 'Overlay file: %s\n' "$output_dir/overlay.html"
  printf 'LaunchAgent: %s\n' "$plist_path"
  printf 'Printer address: %s\n' "$printer_ip"
  exit 0
fi

command -v python3 >/dev/null || { echo "Python 3 is required" >&2; exit 1; }
mkdir -p "$install_dir" "$output_dir" "$log_dir" "$launch_agents"
cp "$skill_dir/scripts/bambu_overlay.py" "$install_dir/bambu_overlay.py"
cp "$skill_dir/requirements.txt" "$install_dir/requirements.txt"

if [[ ! -x "$install_dir/venv/bin/python" ]]; then
  python3 -m venv "$install_dir/venv"
fi
"$install_dir/venv/bin/python" -m pip install --quiet -r "$install_dir/requirements.txt"

export BLO_LABEL="$label"
export BLO_HOME="$HOME"
export BLO_PYTHON="$install_dir/venv/bin/python"
export BLO_SCRIPT="$install_dir/bambu_overlay.py"
export BLO_OUTPUT="$output_dir"
export BLO_STDOUT="$log_dir/stdout.log"
export BLO_STDERR="$log_dir/stderr.log"
export BLO_PRINTER_IP="$printer_ip"
export BLO_PRINTER_SERIAL="$printer_serial"
export BLO_CONFIG="$config_path"
export BLO_PRINTER_NAME="$printer_name"
export BLO_PLIST="$plist_path"

/usr/bin/python3 - <<'PY'
import os
import plistlib

arguments = [
    os.environ["BLO_PYTHON"],
    os.environ["BLO_SCRIPT"],
    "--printer-ip",
    os.environ["BLO_PRINTER_IP"],
    "--output-dir",
    os.environ["BLO_OUTPUT"],
    "--printer-name",
    os.environ["BLO_PRINTER_NAME"],
]
if os.environ.get("BLO_PRINTER_SERIAL"):
    arguments += ["--serial", os.environ["BLO_PRINTER_SERIAL"]]
if os.environ.get("BLO_CONFIG"):
    arguments += ["--config", os.environ["BLO_CONFIG"]]

payload = {
    "Label": os.environ["BLO_LABEL"],
    "ProgramArguments": arguments,
    "RunAtLoad": True,
    "KeepAlive": True,
    "EnvironmentVariables": {"HOME": os.environ["BLO_HOME"]},
    "StandardOutPath": os.environ["BLO_STDOUT"],
    "StandardErrorPath": os.environ["BLO_STDERR"],
}
with open(os.environ["BLO_PLIST"], "wb") as handle:
    plistlib.dump(payload, handle, sort_keys=False)
PY

uid="$(id -u)"
launchctl bootout "gui/$uid" "$plist_path" 2>/dev/null || true
launchctl bootstrap "gui/$uid" "$plist_path"
launchctl kickstart -k "gui/$uid/$label"

printf 'Installed Bambu Live Overlay.\n'
printf 'OBS local browser source: %s\n' "$output_dir/overlay.html"
printf 'Service label: %s\n' "$label"
printf 'Logs: %s\n' "$log_dir"

