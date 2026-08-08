#!/usr/bin/env python3

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "synopsys_compat.py"
SPEC = importlib.util.spec_from_file_location("synopsys_compat", MODULE_PATH)
compat = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
import sys
sys.modules[SPEC.name] = compat
SPEC.loader.exec_module(compat)


SNPS = '''#!/bin/sh
synopsys_install_root_bin="x"
real_synopsys_install_root_bin="x"
if [ T"${real_synopsys_install_root_bin}" == "T" ]; then
  real_synopsys_install_root_bin=x
fi
if [ T"${real_platform}" == "T" ] && [ -f "${real_synopsys_install_root_bin}/bin/snps_platform" ] ; then
  real_platform=x
fi
. "${real_synopsys_install_root_bin}/bin/snps_common.sh"
'''
ICC2 = '''#!/bin/sh
if [[ "$VS" =~ "11" ]] && [[ "$PATCH" =~ "4" ]]; then :; fi
if [ $OS_Version == 1 ]; then :; fi
'''
VCS = '''#!/bin/sh -h
function create_euclide_db() {
  local x
  if [[ -v EUCLIDE_HOME ]]; then :; fi
}
declare -a POST_SCRIPTS
'''
VERDI = '''#!/bin/sh
original_argv=("$@")
while [[ $# -gt 0 ]]; do shift; done
test -r ${interactive_debug_file_eman} && source ${interactive_debug_file_eman}
'''


class UnifiedCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parent = os.environ.get("SYNOPSYS_SKILL_TEST_TMP")
        if not parent:
            raise RuntimeError("SYNOPSYS_SKILL_TEST_TMP must point inside workspace ./tmp")
        cls.parent = Path(parent).resolve()
        cls.parent.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=self.parent)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "Synopsys"
        fixtures = {
            "syn/V-2023.12-SP3/bin/snps_shell": SNPS,
            "lc/V-2023.12-SP3/bin/snps_shell": SNPS,
            "syn/V-2023.12-SP3/icc2/bin/icc2_shell": ICC2,
            "vcs/W-2024.09-SP1/bin/vcs": VCS,
            "verdi/W-2024.09-SP1/bin/.wrapper": VERDI,
        }
        for relative, content in fixtures.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            path.chmod(0o755)

    @property
    def host(self):
        return compat.HostInfo("x86_64", "7.0.0-test", "ubuntu", "26.04")

    def test_all_transforms_are_idempotent(self):
        for item in compat.inspect_targets(self.root):
            self.assertEqual("ORIGINAL", item.state, item.path)
            self.assertTrue(item.changed)
            updated, state, _ = item.spec.transform(item.after.decode())
            self.assertEqual("PATCHED", state)
            self.assertEqual(item.after, updated.encode())

    def test_snps_partial_is_detected(self):
        path = self.root / "syn/V-2023.12-SP3/bin/snps_shell"
        path.write_text(path.read_text().replace('[ T"${real_synopsys_install_root_bin}" == "T" ]', '[ T"${real_synopsys_install_root_bin}" = "T" ]'), encoding="utf-8")
        item = compat.inspect_target(self.root, compat.TARGETS[0])
        self.assertEqual("PARTIAL", item.state)

    def test_duplicate_anchor_is_unexpected(self):
        path = self.root / "vcs/W-2024.09-SP1/bin/vcs"
        path.write_text(path.read_text() + "#!/bin/sh -h\n", encoding="utf-8")
        self.assertEqual("UNEXPECTED", compat.inspect_target(self.root, compat.TARGETS[3]).state)

    def test_malformed_vendor_script_is_blocked_and_isolated(self):
        path = self.root / "vcs/W-2024.09-SP1/bin/vcs"
        path.write_text(path.read_text() + "else\n", encoding="utf-8")
        self.assertEqual("BLOCKED_VENDOR_SCRIPT", compat.inspect_target(self.root, compat.TARGETS[3]).state)
        workspace = self.base / "workspace"
        workspace.mkdir()
        _, _, manifest, inspections = compat.prepare(self.root, str(workspace), self.host, {"dc"})
        self.assertEqual(["dc"], manifest["products"])
        self.assertEqual(["dc"], [item.spec.product for item in inspections])

    def test_elf_architecture_filter_is_exact(self):
        self.assertTrue(compat.is_x86_64_elf({"class": "ELF64", "machine": "Advanced Micro Devices X86-64"}))
        self.assertFalse(compat.is_x86_64_elf({"class": "ELF64", "machine": "AArch64"}))
        self.assertFalse(compat.is_x86_64_elf({"class": "ELF32", "machine": "Intel 80386"}))
        self.assertFalse(compat.is_x86_64_elf(None))

    def test_elf_metadata_forces_stable_c_locale(self):
        fake = self.base / "libsample.so.1"
        fake.write_bytes(b"ELF fixture")
        header = mock.Mock(returncode=0, stdout="  Class: ELF64\n  Machine: Advanced Micro Devices X86-64\n")
        dynamic = mock.Mock(returncode=0, stdout=" 0 (NEEDED) Shared library: [libc.so.6]\n 0 (SONAME) Library soname: [libsample.so.1]\n")
        with mock.patch.object(compat.shutil, "which", return_value="/usr/bin/readelf"):
            with mock.patch.object(compat.subprocess, "run", side_effect=[header, dynamic]) as run:
                value = compat.elf_metadata(fake)
        self.assertEqual("libsample.so.1", value["soname"])
        self.assertEqual(["libc.so.6"], value["needed"])
        for call in run.call_args_list:
            self.assertEqual("C", call.kwargs["env"]["LC_ALL"])
            self.assertEqual("C", call.kwargs["env"]["LANG"])

    def test_candidate_product_classification(self):
        self.assertEqual("dc", compat.candidate_product(self.root, self.root / "syn/V-2023.12-SP3/linux64/libx.so"))
        self.assertEqual("icc2", compat.candidate_product(self.root, self.root / "syn/V-2023.12-SP3/icc2/linux64/libx.so"))
        self.assertEqual("verdi", compat.candidate_product(self.root, self.root / "verdi_supp/W-2024.09-SP1/linux64/libx.so"))
        self.assertIsNone(compat.candidate_product(self.root, self.base / "outside/libx.so"))

    def test_symlink_is_rejected(self):
        path = self.root / "verdi/W-2024.09-SP1/bin/.wrapper"
        other = self.base / "other"
        other.write_text("safe", encoding="utf-8")
        path.unlink()
        path.symlink_to(other)
        self.assertEqual("UNEXPECTED", compat.inspect_target(self.root, compat.TARGETS[4]).state)
        self.assertEqual("safe", other.read_text())

    def test_host_gate_is_exact(self):
        self.assertTrue(self.host.eligible)
        self.assertFalse(compat.HostInfo("x86_64", "6.0", "ubuntu", "26.04").eligible)
        self.assertFalse(compat.HostInfo("aarch64", "7.0", "ubuntu", "26.04").eligible)
        self.assertFalse(compat.HostInfo("x86_64", "7.0", "ubuntu", "24.04").eligible)

    def test_apply_and_rollback(self):
        workspace = self.base / "workspace"
        workspace.mkdir()
        originals = {str(i.path): i.path.read_bytes() for i in compat.inspect_targets(self.root)}
        _, manifest_path, manifest, _ = compat.prepare(self.root, str(workspace), self.host)
        compat.install(manifest_path, manifest)
        self.assertTrue(all(i.state == "PATCHED" for i in compat.inspect_targets(self.root)))
        committed = compat.load_manifest(manifest_path)
        compat.rollback(manifest_path, committed)
        for name, data in originals.items():
            self.assertEqual(data, Path(name).read_bytes())

    def test_install_failure_restores_previous_files(self):
        workspace = self.base / "workspace"
        workspace.mkdir()
        originals = {str(i.path): i.path.read_bytes() for i in compat.inspect_targets(self.root)}
        _, manifest_path, manifest, _ = compat.prepare(self.root, str(workspace), self.host)
        real_replace = compat.os.replace
        calls = 0

        def fail(src, dst):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise OSError("injected")
            return real_replace(src, dst)

        with mock.patch.object(compat.os, "replace", side_effect=fail):
            with self.assertRaises(OSError):
                compat.install(manifest_path, manifest)
        for name, data in originals.items():
            self.assertEqual(data, Path(name).read_bytes())
        self.assertEqual("restored_after_failure", compat.load_manifest(manifest_path)["status"])

    def test_rollback_refuses_drift(self):
        workspace = self.base / "workspace"
        workspace.mkdir()
        _, manifest_path, manifest, _ = compat.prepare(self.root, str(workspace), self.host)
        compat.install(manifest_path, manifest)
        path = self.root / "vcs/W-2024.09-SP1/bin/vcs"
        path.write_text(path.read_text() + "# drift\n", encoding="utf-8")
        with self.assertRaisesRegex(compat.SafetyError, "post-apply drift"):
            compat.rollback(manifest_path, compat.load_manifest(manifest_path))

    def test_false_soname_is_rejected(self):
        fake = self.base / "libtinfo.so.5"
        fake.write_text("not an ELF", encoding="utf-8")
        self.assertIsNone(compat.elf_soname(fake))

    def test_source_has_no_xilinx_or_system_tmp(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("/opt/eda/Xilinx", source)
        self.assertNotIn('Path("/tmp") /', source)
        self.assertNotRegex(source, r"(?:\.zshrc|\.bashrc)")

    def test_workspace_scoped_temp_environment(self):
        run = self.base / "workspace/tmp/run"
        run.mkdir(parents=True)
        env = compat.temp_env(run)
        for key in ("TMPDIR", "TMP", "TEMP"):
            self.assertTrue(Path(env[key]).is_relative_to(run))

    def test_manifest_rejects_wrong_skill(self):
        path = self.base / "manifest.json"
        path.write_text(json.dumps({"schema": 1, "skill": "other"}), encoding="utf-8")
        with self.assertRaises(compat.SafetyError):
            compat.load_manifest(path)


if __name__ == "__main__":
    unittest.main()
