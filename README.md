# Bambu Live Overlay

[![skills.sh](https://skills.sh/b/Sanwanh/bambu-live-overlay)](https://skills.sh/Sanwanh/bambu-live-overlay)

An Agent Skill that sets up a local, automatically updating Bambu Lab printer-status card in OBS for YouTube and other live streams.

It reads the printer's LAN MQTT status, renders a transparent browser overlay, helps configure the Bambu Studio virtual camera, and verifies the result from printer to streaming preview.

## Install the Skill

```bash
npx skills add Sanwanh/bambu-live-overlay
```

Then invoke it in a compatible agent:

```text
Use $bambu-live-overlay to add my Bambu Lab printer status to OBS.
```

## What the overlay shows

- Print job and state
- Percentage and progress bar
- Current and total layers
- Remaining time
- Nozzle and bed temperatures

## Supported setup

- macOS: automated background-service installer
- Windows and Linux: portable Python runtime with manual/service guidance
- OBS Browser Source: transparent 900×160 card
- Bambu Studio local/LAN access: no Bambu Cloud credential upload

## Security

The repository contains no printer serials, access codes, stream keys, account data, or fixed private-network addresses. The runtime reads the Bambu Studio local access code only on the user's computer and connects directly to the printer over the local network.

Review the Skill and scripts before installing. Do not expose Bambu MQTT port `8883` to the public internet.

## License

MIT

