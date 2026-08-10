#!/usr/bin/env python3

import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "qqmusic_fix.py"
SPEC = importlib.util.spec_from_file_location("qqmusic_fix", MODULE_PATH)
fix = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
import sys
sys.modules[SPEC.name] = fix
SPEC.loader.exec_module(fix)


def fake_result(output: str, code: int = 1):
    return mock.Mock(returncode=code, stdout=output, stderr="", args=[], timeout=None)


class QqmusicLaunchFixTests(unittest.TestCase):
    def setUp(self):
        self.parent = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: None)

    def test_classify_gpu_crash(self):
        info = fix.classify("FATAL:gpu_data_manager_impl_private.cc\nThe display compositor is frequently crashing")
        self.assertTrue(info["gpu_crash"])
        self.assertFalse(info["missing_lib"])

    def test_classify_missing_lib(self):
        info = fix.classify("error while loading shared libraries: libfoo.so.1: cannot open shared object file")
        self.assertFalse(info["gpu_crash"])
        self.assertEqual("libfoo.so.1", info["missing_lib"])

    def test_promise_noise_does_not_imply_success(self):
        info = fix.classify("UnhandledPromiseRejectionWarning: undefined\nlogin refresh fail")
        self.assertFalse(info["gpu_crash"])
        self.assertFalse(info["missing_lib"])

    def test_probe_selects_disable_gpu_sandbox(self):
        out = "FATAL:gpu_data_manager_impl_private.cc\nThe display compositor is frequently crashing"
        good = fake_result("(electron) UnhandledPromiseRejectionWarning\napp.ready")
        with mock.patch.object(fix, "run", side_effect=[fake_result(out), fake_result(out), fake_result(out), good]):
            probe = fix.probe_params("/opt/qqmusic/qqmusic")
        self.assertTrue(probe["ok"])
        self.assertIn("--disable-gpu-sandbox", probe["parameter"])

    def test_probe_reports_failure_when_none_work(self):
        out = "The display compositor is frequently crashing"
        with mock.patch.object(fix, "run", return_value=fake_result(out)):
            probe = fix.probe_params("/opt/qqmusic/qqmusic")
        self.assertFalse(probe["ok"])

    def test_confirm_method_refuses_missing_lib(self):
        with mock.patch.object(fix, "run", return_value=fake_result("error while loading shared libraries: libz.so.1")):
            with self.assertRaises(fix.SafetyError):
                fix.confirm_method("/opt/qqmusic/qqmusic")

    def test_apply_launcher_creates_user_copy(self):
        stock = self.parent / "qqmusic.desktop"
        stock.write_text('Exec=/opt/qqmusic/qqmusic %U\n', encoding="utf-8")
        home = self.parent / "home"
        outcome = fix.apply_launcher(stock, ["--disable-gpu-sandbox"], home=home)
        self.assertTrue(outcome["changed"])
        target = home / ".local/share/applications/qqmusic.desktop"
        self.assertEqual('Exec=/opt/qqmusic/qqmusic --disable-gpu-sandbox %U\n', target.read_text(encoding="utf-8"))

    def test_apply_launcher_does_not_overwrite_existing(self):
        stock = self.parent / "qqmusic.desktop"
        stock.write_text('Exec=/opt/qqmusic/qqmusic %U\n', encoding="utf-8")
        home = self.parent / "home"
        fix.apply_launcher(stock, ["--disable-gpu-sandbox"], home=home)
        second = fix.apply_launcher(stock, ["--disable-gpu-sandbox"], home=home)
        self.assertFalse(second["changed"])

    def test_source_does_not_touch_system_desktop_or_sudo(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("/usr/share/applications/qqmusic.desktop", source)
        self.assertNotIn("sudo", source)


if __name__ == "__main__":
    unittest.main()
