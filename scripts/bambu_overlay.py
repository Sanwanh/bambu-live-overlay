#!/usr/bin/env python3
"""Render Bambu Lab LAN MQTT status as a transparent OBS browser overlay."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import signal
import ssl
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

try:
    import paho.mqtt.client as mqtt
except ImportError as exc:  # pragma: no cover - exercised by operator setup
    raise SystemExit("Missing dependency: run `python -m pip install -r requirements.txt`") from exc


TRACKED_FIELDS = {
    "gcode_state",
    "mc_percent",
    "mc_remaining_time",
    "layer_num",
    "total_layer_num",
    "nozzle_temper",
    "bed_temper",
    "subtask_name",
}

STATE_LABELS = {
    "RUNNING": "Printing",
    "PAUSE": "Paused",
    "FINISH": "Finished",
    "FAILED": "Failed",
    "IDLE": "Idle",
}


def config_candidates() -> list[Path]:
    home = Path.home()
    appdata = os.environ.get("APPDATA")
    paths = [
        home / "Library/Application Support/BambuStudio/BambuStudio.conf",
        home / ".config/BambuStudio/BambuStudio.conf",
        home / ".config/bambu-studio/BambuStudio.conf",
    ]
    if appdata:
        paths.insert(0, Path(appdata) / "BambuStudio/BambuStudio.conf")
    return paths


def locate_config(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Bambu Studio config not found: {path}")
        return path
    for path in config_candidates():
        if path.is_file():
            return path
    raise FileNotFoundError(
        "Bambu Studio config was not found. Start Bambu Studio once or pass --config."
    )


def load_credentials(config_path: Path, requested_serial: str | None) -> tuple[str, str]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    access_codes = config.get("access_code") or {}
    preferred = list((config.get("user_access_code") or {}).keys())
    candidates = preferred + [key for key in access_codes if key not in preferred]

    if requested_serial:
        if requested_serial not in access_codes:
            raise RuntimeError("The requested printer serial has no local access code in Bambu Studio.")
        serial = requested_serial
    elif len(candidates) == 1:
        serial = candidates[0]
    elif not candidates:
        raise RuntimeError(
            "No local Bambu access code was found. Enable LAN access in Bambu Studio or on the printer."
        )
    else:
        joined = ", ".join(candidates)
        raise RuntimeError(f"Multiple printers are configured. Re-run with --serial using one of: {joined}")

    password = access_codes.get(serial)
    if not isinstance(password, str) or not password:
        raise RuntimeError("The selected printer has no usable local access code.")
    return serial, password


def validate_printer_host(host: str, allow_public: bool) -> str:
    value = host.strip()
    if not value or re.search(r"\s", value):
        raise ValueError("Printer address is empty or invalid.")
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        if not re.fullmatch(r"[A-Za-z0-9._-]+", value):
            raise ValueError("Printer hostname contains unsupported characters.")
        return value
    if not allow_public and not (address.is_private or address.is_link_local or address.is_loopback):
        raise ValueError(
            "Refusing a public printer IP. Use a LAN/VPN address or pass --allow-public only after verification."
        )
    return value


def as_number(value: Any, fallback: str = "--") -> str:
    if value is None:
        return fallback
    try:
        return str(int(round(float(value))))
    except (TypeError, ValueError):
        return str(value)


def remaining_text(value: Any) -> str:
    try:
        total = max(0, int(float(value)))
    except (TypeError, ValueError):
        return "--"
    hours, minutes = divmod(total, 60)
    return f"{hours}h {minutes:02d}m" if hours else f"{minutes}m"


def display_model(status: dict[str, Any], fallback_name: str = "Bambu printer") -> dict[str, Any]:
    state_raw = str(status.get("gcode_state") or "CONNECTING")
    percent_value = status.get("mc_percent")
    try:
        percent = max(0, min(100, int(round(float(percent_value)))))
    except (TypeError, ValueError):
        percent = 0
    return {
        "printer": fallback_name,
        "job": str(status.get("subtask_name") or "Waiting for job data"),
        "state": STATE_LABELS.get(state_raw, state_raw.replace("_", " ").title()),
        "percent": percent,
        "layer": as_number(status.get("layer_num")),
        "layers": as_number(status.get("total_layer_num")),
        "remaining": remaining_text(status.get("mc_remaining_time")),
        "nozzle": as_number(status.get("nozzle_temper")),
        "bed": as_number(status.get("bed_temper")),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def render_text(model: dict[str, Any]) -> str:
    return (
        f"{model['printer']} | {model['job']}\n"
        f"{model['state']} {model['percent']}% | Layer {model['layer']}/{model['layers']} | "
        f"Remaining {model['remaining']} | Nozzle {model['nozzle']} C | Bed {model['bed']} C\n"
    )


def render_html(model: dict[str, Any], accent: str) -> str:
    title = escape(f"{model['printer']} | {model['job']}")
    detail = escape(
        f"{model['state']}  {model['percent']}%  |  Layer {model['layer']}/{model['layers']}  |  "
        f"Remaining {model['remaining']}  |  Nozzle {model['nozzle']}°C  |  Bed {model['bed']}°C"
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="2">
<style>
html,body{{width:100%;height:100%;margin:0;overflow:hidden;background:transparent;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#fff}}
.card{{box-sizing:border-box;width:calc(100% - 24px);margin:12px;padding:18px 22px 16px;border:1px solid rgba(255,255,255,.18);border-radius:18px;background:linear-gradient(135deg,rgba(8,12,16,.88),rgba(22,29,34,.76));box-shadow:0 10px 30px rgba(0,0,0,.42)}}
.title{{font-size:29px;line-height:1.15;font-weight:750;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.detail{{margin-top:9px;font-size:23px;line-height:1.2;font-weight:600;color:rgba(255,255,255,.92);white-space:nowrap}}
.bar{{height:7px;margin-top:13px;overflow:hidden;border-radius:99px;background:rgba(255,255,255,.16)}}
.fill{{height:100%;width:{model['percent']}%;border-radius:inherit;background:{accent}}}
</style></head><body><section class="card"><div class="title">{title}</div><div class="detail">{detail}</div><div class="bar"><div class="fill"></div></div></section></body></html>"""


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_outputs(output_dir: Path, model: dict[str, Any], accent: str) -> None:
    atomic_write(output_dir / "status.txt", render_text(model))
    atomic_write(output_dir / "status.json", json.dumps(model, ensure_ascii=False, indent=2) + "\n")
    atomic_write(output_dir / "overlay.html", render_html(model, accent))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--printer-ip", default=os.environ.get("BAMBU_PRINTER_IP"))
    parser.add_argument("--serial", default=os.environ.get("BAMBU_SERIAL"))
    parser.add_argument("--config", default=os.environ.get("BAMBU_CONFIG"))
    parser.add_argument(
        "--output-dir",
        default=os.environ.get("BAMBU_OVERLAY_DIR", str(Path.cwd() / "bambu-overlay-output")),
    )
    parser.add_argument("--printer-name", default=os.environ.get("BAMBU_PRINTER_NAME", "Bambu printer"))
    parser.add_argument("--accent", default="#65D38E")
    parser.add_argument("--allow-public", action="store_true")
    parser.add_argument("--demo", action="store_true", help="Write sample output and exit without MQTT")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", args.accent):
        raise SystemExit("--accent must be a six-digit hex color such as #65D38E")
    output_dir = Path(args.output_dir).expanduser().resolve()

    if args.demo:
        sample = {
            "gcode_state": "RUNNING",
            "mc_percent": 54,
            "mc_remaining_time": 224,
            "layer_num": 137,
            "total_layer_num": 350,
            "nozzle_temper": 220,
            "bed_temper": 55,
            "subtask_name": "Demo print",
        }
        write_outputs(output_dir, display_model(sample, args.printer_name), args.accent)
        print(output_dir / "overlay.html")
        return 0

    if not args.printer_ip:
        raise SystemExit("--printer-ip is required (or set BAMBU_PRINTER_IP).")
    host = validate_printer_host(args.printer_ip, args.allow_public)
    config_path = locate_config(args.config)
    serial, password = load_credentials(config_path, args.serial)

    status: dict[str, Any] = {}
    changed = threading.Event()
    stopping = threading.Event()

    def publish_model(message: str | None = None) -> None:
        model = display_model(status, args.printer_name)
        if message:
            model["job"] = message
        write_outputs(output_dir, model, args.accent)

    def on_connect(client, userdata, flags, reason_code, properties=None):
        if getattr(reason_code, "is_failure", False):
            publish_model("Connection failed; retrying")
            return
        client.subscribe(f"device/{serial}/report")
        request = {
            "pushing": {
                "sequence_id": str(int(time.time())),
                "command": "pushall",
                "version": 1,
                "push_target": 1,
            }
        }
        client.publish(f"device/{serial}/request", json.dumps(request))

    def on_disconnect(client, userdata, disconnect_flags, reason_code, properties=None):
        if not stopping.is_set():
            publish_model("Temporarily offline; reconnecting")

    def on_message(client, userdata, message):
        try:
            payload = json.loads(message.payload.decode("utf-8", "replace"))
            report = payload.get("print", payload)
            before = dict(status)
            status.update({key: report[key] for key in TRACKED_FIELDS if key in report})
            if status != before:
                changed.set()
        except Exception:
            return

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set("bblp", password)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    def stop_handler(signum, frame):
        stopping.set()
        changed.set()

    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    publish_model("Connecting to printer")
    client.connect_async(host, 8883, keepalive=20)
    client.loop_start()
    try:
        while not stopping.is_set():
            if changed.wait(timeout=5):
                changed.clear()
                if status:
                    write_outputs(output_dir, display_model(status, args.printer_name), args.accent)
    finally:
        stopping.set()
        client.loop_stop()
        client.disconnect()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"bambu-live-overlay: {exc}", file=sys.stderr)
        raise SystemExit(1)

