---
name: bambu-live-overlay
description: Set up a local Bambu Lab printer status overlay for OBS and live streams, including LAN MQTT status, Bambu Studio virtual camera, macOS background service installation, and end-to-end preview verification. Use for Bambu printer monitoring overlays; do not use for remote printer control or cloud credential sharing.
---

# Bambu Live Overlay

Create a readable, automatically updating Bambu Lab status card over the printer camera without exposing printer credentials or stream keys.

## Scope and routing

- For macOS installation, read [references/platforms.md](references/platforms.md), then use `scripts/install_macos.sh`.
- For Windows, Linux, manual runs, or printer-IP discovery, read [references/platforms.md](references/platforms.md).
- When configuring OBS, Bambu Studio Virtual Camera, or YouTube, read [references/obs-youtube.md](references/obs-youtube.md).
- When the card is blank, stale, disconnected, or the stream is unhealthy, read [references/troubleshooting.md](references/troubleshooting.md).

Do not install persistent services, change OBS, or start/stop a stream unless that action is within the user's request. Do not treat permission to set up an overlay as permission to publish publicly.

## Workflow

1. Determine the operating system and confirm Bambu Studio and OBS are installed.
2. Resolve the printer's LAN address. Prefer an existing Bambu Studio MQTT connection or the address shown on the printer. Ask the user only when no single address can be identified safely.
3. Confirm Bambu Studio has a local access code. Never print, log, commit, paste into chat, or transmit the access code.
4. Install or run `scripts/bambu_overlay.py`:
   - On macOS, run `scripts/install_macos.sh --printer-ip <LAN-IP>` after the user has requested a complete installation.
   - On other platforms, create a virtual environment, install `requirements.txt`, and run the script with `--printer-ip` and an output directory.
5. Verify `overlay.html`, `status.txt`, and `status.json` update. Use `--demo` first if OBS rendering must be tested without connecting to a printer.
6. Configure the Bambu Studio virtual camera and OBS according to [references/obs-youtube.md](references/obs-youtube.md).
7. Verify in layers: local status files, OBS preview, then the streaming platform preview. A configured source is not complete until its visible content is confirmed.
8. Report the current printer state, overlay location, service state, and any remaining stream-health warnings.

## Security and privacy invariants

- Read credentials at runtime from the user's Bambu Studio configuration, or from explicit environment variables. Never copy credentials into the skill, source code, Git history, screenshots, logs, or a browser form.
- Connect directly to the printer on the local network. Reject a public IP by default; proceed only if the user explicitly confirms a trusted private-network route such as a VPN.
- Do not expose the printer MQTT port to the internet.
- Do not reveal YouTube stream keys. Treat stream keys as passwords.
- Distinguish YouTube **Private** from **Unlisted**: Private restricts viewers to invited accounts, while Unlisted is accessible to anyone with the link.
- Do not add music unless the user supplies it or its license clearly permits live-stream use. Keep proof of the license when appropriate.
- Screen lock alone is compatible with streaming, but sleep, logout, OBS exit, network loss, or a system restart can interrupt it.

## Expected outputs

The runtime writes three local files:

- `overlay.html`: transparent 900×160 browser-source card with progress bar.
- `status.txt`: two-line human-readable status.
- `status.json`: structured status plus update time.

The card should show job name, state, percentage, layer, remaining time, nozzle temperature, and bed temperature. Missing fields must render as `--`, not crash the service.
