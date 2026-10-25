# Platform setup and printer discovery

## Prerequisites

- Bambu Studio signed in to, or paired with, the printer.
- LAN access enabled and a local access code present.
- Python 3.9 or newer.
- OBS Studio for compositing and streaming.
- The computer and printer on the same trusted LAN, or connected through a trusted VPN.

The runtime connects to the printer's local MQTT TLS port `8883`. It reads status only; it does not publish print-control commands beyond Bambu's `pushall` status request.

## Resolve the printer address

Use the first authoritative source available:

1. Printer network settings.
2. Bambu Studio device details.
3. An existing Bambu Studio MQTT connection.

On macOS, an agent may inspect existing connections without revealing credentials:

```bash
lsof -nP -iTCP:8883 -sTCP:ESTABLISHED
```

On Linux:

```bash
ss -tnp '( dport = :8883 )'
```

On Windows PowerShell:

```powershell
Get-NetTCPConnection -RemotePort 8883 -State Established
```

If more than one printer is present, ask the user which device to use. Do not scan the full network as a default discovery method.

## macOS persistent installation

Run from the skill directory:

```bash
./scripts/install_macos.sh --printer-ip 192.168.x.x --printer-name "Bambu printer"
```

The installer creates:

- Runtime: `~/Library/Application Support/BambuLiveOverlay`
- Overlay: `~/Library/Application Support/BambuLiveOverlay/output/overlay.html`
- LaunchAgent: `~/Library/LaunchAgents/com.bambu-live-overlay.agent.plist`
- Logs: `~/Library/Logs/BambuLiveOverlay`

It stores the printer address and display name in the local LaunchAgent arguments. It does not store an access code; the runtime reads that from Bambu Studio each time it starts.

Validate service and output:

```bash
launchctl print "gui/$(id -u)/com.bambu-live-overlay.agent"
cat "$HOME/Library/Application Support/BambuLiveOverlay/output/status.txt"
```

## Manual or non-macOS run

From the skill directory:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/bambu_overlay.py \
  --printer-ip 192.168.x.x \
  --output-dir ./bambu-overlay-output
```

On Windows, activate the virtual environment or invoke `.venv\\Scripts\\python.exe` directly. Keep the process running while streaming, or create an OS-native service only when the user asks for persistence.

## Demo and multi-printer use

Generate a non-networked sample card:

```bash
python3 scripts/bambu_overlay.py --demo --output-dir ./bambu-overlay-output
```

If Bambu Studio contains multiple access codes, the runtime reports the available serials and requires `--serial`. Never copy those serials into public bug reports or Git commits.

