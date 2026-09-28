#!/usr/bin/env python3
"""Validate launcher gates without starting the client; files stay in workspace/tmp."""
import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import runpy
import tempfile
from unittest.mock import patch

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--workspace", type=Path, required=True)
args = parser.parse_args()
workspace = args.workspace.resolve(strict=True)
root = Path(tempfile.mkdtemp(prefix="sigchld-skill-tests-", dir=workspace / "tmp"))
home = root / "home"
fix = home / ".local/share/chatgpt-sigchld-fix"
fix.mkdir(parents=True)
(fix / "workspace-root").write_text(str(root))
config = home / ".config"
config.mkdir()
(config / "chatgpt-flags.conf").write_text("# comment\n --disable-gpu \n$(touch should-not-exist)\n")
actual = hashlib.file_digest(open("/usr/lib/chatgpt/ChatGPT", "rb"), "sha256").hexdigest()
launcher = Path(__file__).with_name("launcher.py")
for expected, preload, should_load in [(actual, "", True), ("0" * 64, "", False), (actual, "/existing.so", False)]:
    (fix / "binary.sha256").write_text(expected)
    env = {"HOME": str(home), "LD_PRELOAD": preload}
    with patch.dict(os.environ, env, clear=True), patch("sys.argv", [str(launcher), "argument with spaces"]), patch("os.execve") as execute:
        runpy.run_path(str(launcher), run_name="__main__")
    binary, argv, used = execute.call_args.args
    assert argv[1:] == ["--disable-gpu", "$(touch should-not-exist)", "argument with spaces"]
    assert used["LD_PRELOAD"] == (str(fix / "guard.so") if should_load else preload)
    assert Path(used["TMPDIR"]).is_relative_to(root / "tmp")
    assert Path(used["TMPDIR"]).is_dir()
    assert not (root / "should-not-exist").exists()

spec = importlib.util.spec_from_file_location("build_guard", Path(__file__).with_name("build_guard.py"))
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
# A different binary must be rejected before any compiler invocation.
other = root / "unsupported-binary"
other.write_bytes(b"not the tested executable")
with patch.object(build, "BINARY", other), patch("sys.argv", ["build_guard.py", "--workspace", str(root)]), patch.object(build.subprocess, "run") as compiler:
    try:
        build.main()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("unsupported executable was accepted")
    compiler.assert_not_called()
print("PASS: hash mismatch refusal, update bypass, existing preload preservation, literal flags, argument forwarding, workspace temporary directories")
