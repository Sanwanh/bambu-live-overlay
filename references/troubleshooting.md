# Troubleshooting

## Overlay is blank

1. Open `overlay.html` locally and confirm it contains a card.
2. Confirm the OBS Browser Source has **Local file** enabled and points to that exact file.
3. Refresh the Browser Source.
4. Check that the source is visible, above the camera source, and inside the canvas.
5. Use `--demo` to separate OBS rendering from printer connectivity.

On macOS, background jobs may be denied access to `Documents`, `Desktop`, or `Downloads`. Install the runtime under `~/Library/Application Support/BambuLiveOverlay` instead of those privacy-protected folders.

## Status is stale or offline

- Confirm the printer is awake and reachable on the same LAN/VPN.
- Confirm TCP port `8883` is reachable locally.
- Confirm Bambu Studio still contains the local access code.
- Check the background service and logs without printing environment variables or configuration contents.
- Restart only the overlay service first; avoid interrupting OBS or the stream unnecessarily.

## Multiple printers

Run with `--serial <serial>` after selecting the intended printer. Treat serial numbers as private identifiers and do not publish them.

## OBS source updates once but not again

The generated HTML refreshes itself every two seconds. Confirm OBS is reading the stable `overlay.html` path. The runtime replaces that file atomically; do not point OBS at a temporary file whose name changes.

## YouTube says stream health is poor

Inspect the exact warning. For a keyframe/GOP warning, set the OBS keyframe interval to 2 seconds in the streaming encoder settings. Avoid changing encoder settings mid-stream unless the user accepts a possible interruption.

