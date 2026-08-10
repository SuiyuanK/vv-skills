#!/usr/bin/env python3
"""Transactional QQ Music launch fix adapter for Ubuntu 26.04 (x86_64, Linux kernel 7)."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

SKILL = "qqmusic-linux-fix"
SCHEMA = 1
DEFAULT_BIN = "/opt/qqmusic/qqmusic"
EXIT_OK = 0
EXIT_BLOCKED = 3
GPU_CRASH = re.compile(
    r"The display compositor is frequently crashing|"
    r"gpu_data_manager_impl_private\.cc",
    re.I,
)
MISSING_LIB = re.compile(
    r"error while loading shared libraries: ([\w.\-]+)|"
    r"cannot open shared object file",
    re.I,
)


class SafetyError(RuntimeError):
    pass


@dataclass(frozen=True)
class HostInfo:
    arch: str
    os_id: str
    version_id: str
    kernel_major: str

    @property
    def eligible(self) -> bool:
        return (
            self.arch == "x86_64"
            and self.os_id == "ubuntu"
            and self.version_id == "26.04"
            and self.kernel_major == "7"
        )


def read_os_release(path: Path = Path("/etc/os-release")) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return values
    for line in lines:
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"')
    return values


def host_info() -> HostInfo:
    release = read_os_release()
    kernel = subprocess.run(
        ["uname", "-r"], capture_output=True, text=True, check=False
    ).stdout.strip()
    major = kernel.split(".", 1)[0]
    return HostInfo(
        subprocess.run(
            ["uname", "-m"], capture_output=True, text=True, check=False
        ).stdout.strip(),
        release.get("ID", ""),
        release.get("VERSION_ID", ""),
        major,
    )


def which_args(bin_path: str, parameter: str, extra: list[str] | None = None) -> list[str]:
    return [bin_path, parameter, *(extra or [])]


def run(bin_path: str, args: list[str], timeout: int = 25) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["LC_ALL"] = "C"
    env["LANG"] = "C"
    return subprocess.run(
        [bin_path, *args],
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def classify(output: str) -> dict:
    loader = MISSING_LIB.search(output)
    return {
        "gpu_crash": bool(GPU_CRASH.search(output)),
        "missing_lib": loader.group(1) if loader else None,
        "promise_noise": "UnhandledPromiseRejectionWarning" in output,
    }


def probe_params(bin_path: str) -> dict:
    """Return the parameter that launches QQ Music without a GPU crash."""
    candidates = [
        ("-disable-gpu-and-compositing", ["--disable-gpu", "--disable-gpu-compositing"]),
        ("-disable-gpu-x11", ["--disable-gpu", "--disable-gpu-compositing", "--ozone-platform=x11"]),
        ("-swiftshader", ["--use-gl=swiftshader", "--disable-gpu-sandbox"], True),
        ("-disable-gpu-sandbox", ["--disable-gpu-sandbox"]),
    ]
    for name, extra, *rest in candidates:
        args = which_args(bin_path, extra[0], extra[1:])
        try:
            result = run(bin_path, args)
        except subprocess.TimeoutExpired:
            return {"ok": True, "parameter": args[1:], "candidate": name, "timeout": True}
        info = classify(result.stdout + result.stderr)
        if not info["gpu_crash"]:
            return {"ok": True, "parameter": args[1:], "candidate": name, "timeout": False}
    return {"ok": False, "parameter": None, "candidate": None, "timeout": False}


def workdir(workspace: str | None) -> Path:
    base = Path(workspace).expanduser().resolve() if workspace else Path.cwd().resolve()
    result = base / "tmp" / SKILL
    result.mkdir(parents=True, exist_ok=True)
    return result


def confirm_method(bin_path: str) -> dict:
    info = classify(run(bin_path, []).stdout + run(bin_path, []).stderr)
    if info.get("missing_lib"):
        raise SafetyError(
            f"QQ Music is missing dynamic library {info['missing_lib']!r}; "
            f"this is a dependency problem, not a GPU crash."
        )
    probe = probe_params(bin_path)
    return {
        "bin": bin_path,
        "diagnosis": info,
        "probe": probe,
        "parameter": probe.get("parameter"),
        "ok": bool(probe.get("ok")),
    }


def apply_launcher(
    desktop_path: Path,
    parameter: list[str],
    home: Path = Path.home(),
    workspaces: Path | None = None,
) -> dict:
    target = home / ".local/share/applications" / desktop_path.name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return {"status": "exists", "path": str(target), "changed": False}
    shutil.copy(desktop_path, target)
    content = target.read_text(encoding="utf-8")
    old = re.search(r"^Exec=.*$", content, re.M)
    if not old:
        raise SafetyError(f"no Exec= line in {desktop_path}")
    parts = old.group(0)[5:].split()
    if not parts:
        raise SafetyError(f"empty Exec= line in {desktop_path}")
    binary, trailing = parts[0], parts[1:]
    new_exec = "Exec=" + " ".join([binary, *parameter, *trailing])
    replace = content.replace(old.group(0), new_exec, 1)
    target.write_text(replace, encoding="utf-8")
    if workspaces:
        log = workspaces / f"apply-{uuid.uuid4().hex[:8]}.json"
        log.write_text(json.dumps({"desktop": str(target), "parameter": parameter}), encoding="utf-8")
    return {"status": "created", "path": str(target), "changed": True, "exec": new_exec}


def command_diagnose(args: argparse.Namespace) -> int:
    host = host_info()
    if not host.eligible:
        raise SafetyError(f"out of scope: {host}")
    result = confirm_method(args.bin)
    print(json.dumps(result, indent=2) if args.json else f"probe: {result['probe']['candidate']}\nparameter: {result['parameter']}")
    return EXIT_OK if result["ok"] else EXIT_BLOCKED


def command_fix(args: argparse.Namespace) -> int:
    host = host_info()
    if not host.eligible:
        raise SafetyError(f"out of scope: {host}")
    result = confirm_method(args.bin)
    if not result["ok"]:
        raise SafetyError("no working GPU-sandbox parameter found; do not modify launcher")
    desktop = args.desktop or first_desktop()
    if not desktop or not desktop.is_file():
        raise SafetyError("qqmusic .desktop not found; pass --desktop")
    outcome = apply_launcher(desktop, result["parameter"], args.home, workdir(args.workspace))
    print(json.dumps(outcome, indent=2) if args.json else json.dumps(outcome, ensure_ascii=False))
    return EXIT_OK


def first_desktop() -> Path | None:
    for base in ("/usr/share/applications", str(Path.home() / ".local/share/applications")):
        for pattern in ("qqmusic.desktop", "qq-music.desktop", "*qq*music*.desktop"):
            for match in sorted(Path(base).glob(pattern)):
                if match.is_file():
                    return match
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    d = sub.add_parser("diagnose", help="launch QQ Music and pick a working GPU parameter")
    d.add_argument("--json", action="store_true")
    d.add_argument("--bin", default=DEFAULT_BIN)
    d.set_defaults(func=command_diagnose)

    f = sub.add_parser("fix", help="apply a user-local launcher override with the GPU parameter")
    f.add_argument("--json", action="store_true")
    f.add_argument("--bin", default=DEFAULT_BIN)
    f.add_argument("--desktop")
    f.add_argument("--home", default=str(Path.home()))
    f.add_argument("--workspace")
    f.set_defaults(func=command_fix)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except SafetyError as exc:
        print(f"SAFETY ERROR: {exc}", file=sys.stderr)
        return EXIT_BLOCKED
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_BLOCKED


if __name__ == "__main__":
    raise SystemExit(main())
