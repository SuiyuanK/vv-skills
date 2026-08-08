#!/usr/bin/env python3

import importlib.util
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "spyglass_compat.py"
SPEC = importlib.util.spec_from_file_location("spyglass_compat", MODULE_PATH)
compat = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
import sys
sys.modules[SPEC.name] = compat
SPEC.loader.exec_module(compat)


ORIGINALS = {
    "lib/SpyGlass/standard-environment.sh": """#!/bin/sh
unameP=`uname -p`
unameM=`uname -m`
platform_species () {
case "$PLAT" in
     Linux-6*)
       echo "Linux4"
       ;;
esac
}
""",
    "bin/spygenlib": """#!/bin/sh
platform_species () {
case "$PLAT" in
Linux-2* | Linux-3* | Linux-4*) species=Linux4 ;;
esac
}
exec "$d2/obj/link.$platform" "$@"
""",
    "bin/.platform_check.sh": """#!/bin/sh -x
platform_check(){
    result=0
    if [ -f /etc/almalinux-release ]; then
        result=1
    #elif [ -f /etc/debian_version ]; then
        :
    fi
    return $result
}
""",
    "bin/spyglass": """#!/bin/sh
id=spyglass
if [[ "$1" == *"$id"* ]]; then
    :
fi
""",
    "bin/spyglass_main": """#!/bin/sh
ary=($LD_PRELOAD)
select_batch() {
    if [ "X$SPYGLASS_USE_TCMALLOC" != X ] && [ -e "$SPYGLASS_HOME/lib/libtcmalloc.so" ] ; then
        :
    fi
}
select_gui() {
        if [ "X$SPYGLASS_USE_TCMALLOC" != X ] && [ -e "$SPYGLASS_HOME/lib/libtcmalloc.so" ]; then
            :
        fi
}
""",
    "bin/spyexplain": """#!/bin/sh
source `dirname $0`/.platform_check.sh
""",
}

PERL_ORIGINAL = """#!/bin/sh
case "$PLAT" in
Linux-2* | Linux-3* | Linux-4* | Linux-5* | Linux-6*) species=Linux4 ;;
*) echo "ERROR(perl): Unknown platform: $PLAT" 1>&2; exit 1;;
esac
exec ${perl_exe} ${perl_SEARCHPATH} "$@"
"""


class CompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_parent = os.environ.get("SPYGLASS_SKILL_TEST_TMP")
        if not test_parent:
            raise RuntimeError("SPYGLASS_SKILL_TEST_TMP must point inside the workspace ./tmp")
        cls.test_parent = Path(test_parent).resolve()
        cls.test_parent.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=self.test_parent)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def make_root(self, name="spyglass", release=compat.RELEASE):
        install = self.base / name / release
        home = install / "SPYGLASS_HOME"
        for relative, content in ORIGINALS.items():
            path = home / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            path.chmod(0o755)
        perl = install / "perl/bin/perl"
        perl.parent.mkdir(parents=True)
        perl.write_text(PERL_ORIGINAL, encoding="utf-8")
        perl.chmod(0o755)
        return compat.normalize_root(install)

    def patched_text(self, spec, text):
        result, state, _ = spec.transform(text)
        self.assertEqual("ORIGINAL", state)
        result2, state2, _ = spec.transform(result)
        self.assertEqual("PATCHED", state2)
        self.assertEqual(result, result2)
        return result

    def test_every_transform_is_idempotent(self):
        root = self.make_root()
        for target in compat.inspect_roots([root]):
            self.assertEqual("ORIGINAL", target.state, target.path)
            self.assertNotEqual(target.before, target.after)
            transformed, state, _ = target.spec.transform(target.after.decode())
            self.assertEqual("PATCHED", state)
            self.assertEqual(target.after, transformed.encode())

    def test_partial_standard_environment_is_detected(self):
        root = self.make_root()
        spec = next(item for item in compat.TARGETS if item.key == "standard-environment")
        path = spec.path_for(root)
        path.write_text(path.read_text().replace(compat.STD_LINUX_OLD, compat.STD_LINUX_NEW), encoding="utf-8")
        result = compat.inspect_target(root, spec)
        self.assertEqual("PARTIAL", result.state)
        self.assertIn("system_malloc_gate=original", result.reasons)

    def test_partial_spyglass_main_is_detected(self):
        root = self.make_root()
        spec = next(item for item in compat.TARGETS if item.key == "spyglass-main")
        path = spec.path_for(root)
        path.write_text(path.read_text().replace("#!/bin/sh", "#!/bin/bash", 1), encoding="utf-8")
        result = compat.inspect_target(root, spec)
        self.assertEqual("PARTIAL", result.state)

    def test_duplicate_anchor_is_unexpected(self):
        root = self.make_root()
        spec = next(item for item in compat.TARGETS if item.key == "spygenlib")
        path = spec.path_for(root)
        path.write_text(path.read_text().replace(compat.GENLIB_LINUX_OLD, compat.GENLIB_LINUX_OLD + "\n" + compat.GENLIB_LINUX_OLD), encoding="utf-8")
        result = compat.inspect_target(root, spec)
        self.assertEqual("UNEXPECTED", result.state)

    def test_symlink_target_is_unexpected(self):
        root = self.make_root()
        spec = next(item for item in compat.TARGETS if item.key == "spyexplain")
        path = spec.path_for(root)
        other = self.base / "other"
        other.write_text("untouched", encoding="utf-8")
        path.unlink()
        path.symlink_to(other)
        self.assertEqual("UNEXPECTED", compat.inspect_target(root, spec).state)
        self.assertEqual("untouched", other.read_text())

    def test_missing_target_is_reported(self):
        root = self.make_root()
        spec = next(item for item in compat.TARGETS if item.key == "spyglass")
        spec.path_for(root).unlink()
        self.assertEqual("MISSING", compat.inspect_target(root, spec).state)

    def test_unknown_release_is_rejected(self):
        install = self.base / "spyglass/X-2026.01"
        (install / "SPYGLASS_HOME").mkdir(parents=True)
        with self.assertRaises(compat.SafetyError):
            compat.normalize_root(install)

    def test_install_root_and_home_normalize_equally(self):
        root = self.make_root()
        self.assertEqual(root, compat.normalize_root(root.home))
        self.assertEqual(root, compat.normalize_root(root.install))

    def test_host_gate_is_exact(self):
        eligible = compat.HostInfo("x86_64", "7.0.0-29-generic", "ubuntu", "26.04")
        self.assertTrue(eligible.eligible)
        for changed in (
            compat.HostInfo("aarch64", eligible.kernel_release, eligible.os_id, eligible.version_id),
            compat.HostInfo(eligible.arch, "6.14.0", eligible.os_id, eligible.version_id),
            compat.HostInfo(eligible.arch, eligible.kernel_release, "debian", eligible.version_id),
            compat.HostInfo(eligible.arch, eligible.kernel_release, eligible.os_id, "24.04"),
        ):
            self.assertFalse(changed.eligible)

    def test_temp_environment_is_workspace_scoped(self):
        run = self.base / "workspace/tmp/run"
        run.mkdir(parents=True)
        env = compat.temp_env(run, compat.HostInfo("x86_64", "7.0", "ubuntu", "26.04"), system_malloc=True)
        for key in ("TMPDIR", "TMP", "TEMP", "SPYGLASS_TMPDIR"):
            self.assertTrue(Path(env[key]).is_relative_to(run))
        self.assertEqual("1", env["SPYGLASS_USE_SYSTEM_MALLOC"])

    def test_apply_is_idempotent_and_rollback_restores_original(self):
        root = self.make_root()
        original = {str(item.path): item.path.read_bytes() for item in compat.inspect_roots([root])}
        host = compat.HostInfo("x86_64", "7.0", "ubuntu", "26.04")
        workspace = self.base / "workspace"
        workspace.mkdir()
        _, manifest_path, manifest, inspections = compat.prepare_apply([root], str(workspace), host)
        compat.install_prepared(manifest_path, manifest, inspections)
        committed = compat.load_manifest(manifest_path)
        self.assertEqual("committed", committed["status"])
        self.assertTrue(all(item.state == "PATCHED" for item in compat.inspect_roots([root])))

        _, second_manifest_path, second_manifest, second_inspections = compat.prepare_apply([root], str(workspace), host)
        compat.install_prepared(second_manifest_path, second_manifest, second_inspections)
        self.assertFalse(any(entry["changed"] for entry in compat.load_manifest(second_manifest_path)["targets"]))

        compat.rollback_manifest(manifest_path, committed)
        self.assertEqual("rolled_back", compat.load_manifest(manifest_path)["status"])
        for path, content in original.items():
            self.assertEqual(content, Path(path).read_bytes())

    def test_unknown_target_causes_zero_product_writes(self):
        root = self.make_root()
        target = root.home / "bin/spygenlib"
        target.write_text("unexpected", encoding="utf-8")
        before = {str(item.path): item.path.read_bytes() for item in compat.inspect_roots([root]) if item.path.exists() and item.path.is_file()}
        workspace = self.base / "workspace"
        workspace.mkdir()
        with self.assertRaises(compat.SafetyError):
            compat.prepare_apply([root], str(workspace), compat.HostInfo("x86_64", "7.0", "ubuntu", "26.04"))
        for path, content in before.items():
            self.assertEqual(content, Path(path).read_bytes())

    def test_rollback_refuses_post_apply_drift(self):
        root = self.make_root()
        workspace = self.base / "workspace"
        workspace.mkdir()
        host = compat.HostInfo("x86_64", "7.0", "ubuntu", "26.04")
        _, manifest_path, manifest, inspections = compat.prepare_apply([root], str(workspace), host)
        compat.install_prepared(manifest_path, manifest, inspections)
        committed = compat.load_manifest(manifest_path)
        drifted = root.home / "bin/spyexplain"
        drifted.write_text(drifted.read_text() + "# drift\n", encoding="utf-8")
        with self.assertRaisesRegex(compat.SafetyError, "post-apply drift"):
            compat.rollback_manifest(manifest_path, committed)

    def test_install_failure_restores_already_replaced_files(self):
        root = self.make_root()
        workspace = self.base / "workspace"
        workspace.mkdir()
        host = compat.HostInfo("x86_64", "7.0", "ubuntu", "26.04")
        originals = {str(item.path): item.path.read_bytes() for item in compat.inspect_roots([root])}
        _, manifest_path, manifest, inspections = compat.prepare_apply([root], str(workspace), host)
        real_replace = compat.os.replace
        calls = 0

        def failing_replace(src, dst):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise OSError("injected replacement failure")
            return real_replace(src, dst)

        with mock.patch.object(compat.os, "replace", side_effect=failing_replace):
            with self.assertRaises(OSError):
                compat.install_prepared(manifest_path, manifest, inspections)
        for path, content in originals.items():
            self.assertEqual(content, Path(path).read_bytes())
        self.assertEqual("restored_after_failure", compat.load_manifest(manifest_path)["status"])

    def test_runtime_timeout_terminates_process_group(self):
        run = self.base / "run"
        run.mkdir()
        result = compat.run_command(
            "timeout",
            [sys.executable, "-c", "import time; print('READY', flush=True); time.sleep(60)"],
            run,
            os.environ.copy(),
            run / "timeout.log",
            1,
            "READY",
        )
        self.assertTrue(result["timed_out"])
        self.assertEqual(124, result["exit_code"])
        self.assertTrue(result["marker_ok"])
        self.assertFalse(result["crash_signal_6_or_11"])

    def test_signal_6_or_11_text_is_a_crash(self):
        run = self.base / "run"
        run.mkdir()
        result = compat.run_command(
            "crash-marker",
            [sys.executable, "-c", "print('SpyGlass Terminator Signal: 11')"],
            run,
            os.environ.copy(),
            run / "crash.log",
            5,
        )
        self.assertTrue(result["crash_signal_6_or_11"])
        self.assertFalse(result["ok"])

    def test_source_has_no_global_bypass_or_rc_modification(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn('SKIP_PLATFORM_CHECK"] =', source)
        self.assertNotRegex(source, r"(?:\.zshrc|\.bashrc)")
        self.assertNotIn('Path("/tmp") /', source)


if __name__ == "__main__":
    unittest.main()
