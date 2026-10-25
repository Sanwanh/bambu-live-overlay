# OBS, Bambu Studio, and YouTube setup

## Bambu Studio virtual camera

Follow Bambu Lab's current virtual-camera documentation:

<https://wiki.bambulab.com/en/software/bambu-studio/virtual-camera>

When Bambu Studio exposes an SDP file, add it to OBS as a media source using the SDP file URL/path and the FFmpeg input option:

```text
protocol_whitelist=file,udp,rtp
```

On macOS, the SDP file is commonly under:

```text
~/Library/Application Support/BambuStudio/cameratools/ffmpeg.sdp
```

Do not assume that path exists; verify it. Keep Bambu Studio running if the virtual camera depends on it.

## OBS status card

1. Add a **Browser Source** above the printer-camera source.
2. Enable **Local file** and select the generated `overlay.html`.
3. Set width to `900` and height to `160`.
4. Keep the browser background transparent. The default OBS CSS is sufficient.
5. Place the card near the top-left or top-right and keep important print details visible.
6. Refresh the source once, then confirm that a changing layer or percentage appears without another manual refresh.

Do not rely only on the source-properties dialog. Inspect the actual OBS canvas.

## YouTube visibility and go-live boundary

- **Private**: only specified invited accounts can watch.
- **Unlisted**: anyone with the URL can watch, but the stream is not listed publicly.
- **Public**: discoverable by everyone.

If the user says "private link," clarify whether they mean Private or Unlisted before changing visibility. Starting, stopping, or changing the visibility of a live stream is an external side effect; do it only when requested.

After OBS looks correct, verify the YouTube Studio preview. Check that the overlay is readable at the encoded resolution and that the stream is receiving video and audio.

## Stream reliability

- Use a keyframe interval accepted by the platform; YouTube commonly expects 2 seconds and warns when it exceeds 4 seconds.
- Keep the computer awake. Locking the screen is fine if the system does not sleep.
- Keep OBS, the virtual-camera provider, the overlay process, and the network connection running.
- If adding music, use only properly licensed material and keep it below speech or machine-alert levels.

