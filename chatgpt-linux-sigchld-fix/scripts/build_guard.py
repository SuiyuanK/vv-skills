#!/usr/bin/env python3
"""Build the exact known Linux workaround under a task workspace; never install it."""
import argparse
import hashlib
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile

EXPECTED = "23b753552181a8ea661681256c2dbf993fea1285fbc5c824478bad9cbdd45c91"
BINARY = Path("/usr/lib/chatgpt/ChatGPT")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    workspace = args.workspace.resolve(strict=True)
    if not workspace.is_dir() or platform.system() != "Linux" or platform.machine() != "x86_64":
        parser.error("requires an existing workspace and Linux x86-64")
    with BINARY.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != EXPECTED:
        parser.error("unsupported executable SHA-256; diagnose this build instead of changing the pin")
    gcc = shutil.which("gcc")
    if gcc is None:
        parser.error("GCC unavailable; explain dependency and obtain approval before installation")
    temp_root = workspace / "tmp"
    temp_root.mkdir(exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix="chatgpt-sigchld-", dir=temp_root))
    shutil.copyfile(Path(__file__).with_name("guard.c"), output / "guard.c")
    env = os.environ.copy()
    env["TMPDIR"] = str(output)
    subprocess.run([gcc, "-O2", "-fPIC", "-shared", "-Wall", "-Wextra", "-Werror",
                    "-o", str(output / "guard.so"), str(output / "guard.c"), "-ldl"],
                   check=True, env=env)
    (output / "binary.sha256").write_text(EXPECTED + "\n")
    print(output)


if __name__ == "__main__":
    main()
