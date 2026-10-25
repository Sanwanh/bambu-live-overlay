import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "bambu_overlay.py"
SPEC = importlib.util.spec_from_file_location("bambu_overlay", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class OverlayTests(unittest.TestCase):
    def test_display_model_and_render(self):
        status = {
            "gcode_state": "RUNNING",
            "mc_percent": 54,
            "mc_remaining_time": 224,
            "layer_num": 137,
            "total_layer_num": 350,
            "nozzle_temper": 220.2,
            "bed_temper": 55,
            "subtask_name": "Bracket <left>",
        }
        model = MODULE.display_model(status, "H2S")
        self.assertEqual(model["percent"], 54)
        self.assertEqual(model["remaining"], "3h 44m")
        html = MODULE.render_html(model, "#65D38E")
        self.assertIn("Bracket &lt;left&gt;", html)
        self.assertIn("width:54%", html)

    def test_load_credentials_single_printer(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "BambuStudio.conf"
            path.write_text(
                json.dumps({"access_code": {"SERIAL": "secret"}, "user_access_code": {"SERIAL": True}}),
                encoding="utf-8",
            )
            self.assertEqual(MODULE.load_credentials(path, None), ("SERIAL", "secret"))

    def test_demo_writes_all_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            code = MODULE.main(["--demo", "--output-dir", directory, "--printer-name", "H2S"])
            self.assertEqual(code, 0)
            self.assertTrue((Path(directory) / "overlay.html").is_file())
            self.assertTrue((Path(directory) / "status.txt").is_file())
            self.assertTrue((Path(directory) / "status.json").is_file())

    def test_public_ip_rejected(self):
        with self.assertRaises(ValueError):
            MODULE.validate_printer_host("8.8.8.8", allow_public=False)


if __name__ == "__main__":
    unittest.main()

