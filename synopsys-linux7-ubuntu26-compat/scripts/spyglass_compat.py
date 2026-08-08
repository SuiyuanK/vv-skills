#!/usr/bin/env python3
"""Safe SpyGlass X-2025.06 compatibility adapter for Ubuntu 26.04/Linux 7."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import os
import platform
import re
import shutil
import signal
import stat
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Callable, Iterable

SKILL = "spyglass-x2025-linux7-ubuntu26-fix"
RELEASE = "X-2025.06"
DEFAULT_ROOTS = (
    Path("/opt/eda/Synopsys/spyglass/X-2025.06"),
    Path("/opt/eda/Synopsys/ufe_optional_spyglass-vcs/X-2025.06"),
)
EXIT_OK = 0
EXIT_NEEDS_PATCH = 2
EXIT_UNSUPPORTED = 3
EXIT_TRANSACTION = 4
WARNING = (
    "WARNING: Using a local SpyGlass X-2025.06 compatibility adaptation for "
    "Ubuntu 26.04 on x86_64; this is not a Synopsys support certification."
)

STD_LINUX_OLD = "     Linux-6*)"
STD_LINUX_NEW = "     Linux-6* | Linux-7*)"
STD_SYSTEM_ANCHOR = "unameP=`uname -p`\nunameM=`uname -m`\nplatform_species () {"
STD_SYSTEM_BLOCK = """unameP=`uname -p`
unameM=`uname -m`
if [ \"X$unameM\" = \"Xx86_64\" ] && [ -r /etc/os-release ] && \\
   /usr/bin/grep -qx 'ID=ubuntu' /etc/os-release && \\
   /usr/bin/grep -Eq '^VERSION_ID=\"?26\\.04\"?$' /etc/os-release; then
    SPYGLASS_USE_SYSTEM_MALLOC=1
    export SPYGLASS_USE_SYSTEM_MALLOC
fi
platform_species () {"""
PERL_LINUX_OLD = "Linux-2* | Linux-3* | Linux-4* | Linux-5* | Linux-6*)"
PERL_LINUX_NEW = "Linux-2* | Linux-3* | Linux-4* | Linux-5* | Linux-6* | Linux-7*)"
GENLIB_LINUX_OLD = "Linux-2* | Linux-3* | Linux-4*)"
GENLIB_LINUX_NEW = "Linux-2* | Linux-3* | Linux-4* | Linux-5* | Linux-6* | Linux-7*)"
PLATFORM_ANCHOR = "    #elif [ -f /etc/debian_version ]; then"
PLATFORM_BLOCK = """    elif [ -r /etc/os-release ] && \\
         grep -qx 'ID=ubuntu' /etc/os-release && \\
         grep -Eq '^VERSION_ID=\"?26\\.04\"?$' /etc/os-release; then
        echo \"%s\" 1>&2
        result=1
%s""" % (WARNING, PLATFORM_ANCHOR)
MAIN_BATCH_OLD = '    if [ "X$SPYGLASS_USE_TCMALLOC" != X ] && [ -e "$SPYGLASS_HOME/lib/libtcmalloc.so" ] ; then'
MAIN_BATCH_NEW = """    if [ "X$SPYGLASS_USE_SYSTEM_MALLOC" = "X1" ]; then
        :
    elif [ "X$SPYGLASS_USE_TCMALLOC" != X ] && [ -e "$SPYGLASS_HOME/lib/libtcmalloc.so" ] ; then"""
MAIN_GUI_OLD = '        if [ "X$SPYGLASS_USE_TCMALLOC" != X ] && [ -e "$SPYGLASS_HOME/lib/libtcmalloc.so" ]; then'
MAIN_GUI_NEW = """        if [ "X$SPYGLASS_USE_SYSTEM_MALLOC" = "X1" ]; then
            :
        elif [ "X$SPYGLASS_USE_TCMALLOC" != X ] && [ -e "$SPYGLASS_HOME/lib/libtcmalloc.so" ]; then"""


class SafetyError(RuntimeError):
    pass


@dataclasses.dataclass(frozen=True)
class HostInfo:
    arch: str
    kernel_release: str
    os_id: str
    version_id: str

    @property
    def eligible(self) -> bool:
        major = self.kernel_release.split(".", 1)[0]
        return (
            self.arch == "x86_64"
            and self.os_id == "ubuntu"
            and self.version_id == "26.04"
            and major == "7"
        )


@dataclasses.dataclass(frozen=True)
class InstallRoot:
    install: Path
    home: Path


@dataclasses.dataclass(frozen=True)
class TargetSpec:
    key: str
    location: str
    transform: Callable[[str], tuple[str, str, list[str]]]
    syntax: str = "bash"

    def path_for(self, root: InstallRoot) -> Path:
        base = root.install if self.location.startswith("install:") else root.home
        relative = self.location.split(":", 1)[1]
        return base / relative


@dataclasses.dataclass
class Inspection:
    root: InstallRoot
    spec: TargetSpec
    path: Path
    state: str
    reasons: list[str]
    before: bytes | None
    after: bytes | None
    file_stat: os.stat_result | None

    @property
    def changed(self) -> bool:
        return self.before is not None and self.after is not None and self.before != self.after


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def exactly_one(text: str, value: str) -> bool:
    return text.count(value) == 1


def replace_component(text: str, old: str, new: str, name: str) -> tuple[str, str]:
    old_count, new_count = text.count(old), text.count(new)
    if old_count == 1 and new_count == 0:
        return text.replace(old, new, 1), "ORIGINAL"
    if old_count == 0 and new_count == 1:
        return text, "PATCHED"
    raise SafetyError(f"{name}: expected one original or one patched anchor, got old={old_count}, new={new_count}")


def transform_standard(text: str) -> tuple[str, str, list[str]]:
    if "platform_species ()" not in text or "echo \"Linux4\"" not in text:
        raise SafetyError("standard-environment: required Linux4 taxonomy anchors are missing")
    updated, linux_state = replace_component(text, STD_LINUX_OLD, STD_LINUX_NEW, "standard Linux7")
    updated, malloc_state = replace_component(updated, STD_SYSTEM_ANCHOR, STD_SYSTEM_BLOCK, "system malloc host gate")
    state = "PATCHED" if linux_state == malloc_state == "PATCHED" else "ORIGINAL" if linux_state == malloc_state == "ORIGINAL" else "PARTIAL"
    reasons = [f"linux7={linux_state.lower()}", f"system_malloc_gate={malloc_state.lower()}"]
    return updated, state, reasons


def transform_perl(text: str) -> tuple[str, str, list[str]]:
    if 'echo "ERROR(perl): Unknown platform: $PLAT"' not in text or "exec ${perl_exe} ${perl_SEARCHPATH}" not in text:
        raise SafetyError("bundled Perl wrapper identity anchors are missing")
    updated, state = replace_component(text, PERL_LINUX_OLD, PERL_LINUX_NEW, "Perl Linux7")
    return updated, state, [f"linux7={state.lower()}"]


def transform_spygenlib(text: str) -> tuple[str, str, list[str]]:
    if 'exec "$d2/obj/link.$platform" "$@"' not in text or "platform_species ()" not in text:
        raise SafetyError("spygenlib identity anchors are missing")
    updated, state = replace_component(text, GENLIB_LINUX_OLD, GENLIB_LINUX_NEW, "spygenlib Linux7")
    return updated, state, [f"linux7={state.lower()}"]


def transform_platform(text: str) -> tuple[str, str, list[str]]:
    if "platform_check(){" not in text or "return $result" not in text:
        raise SafetyError("platform check identity anchors are missing")
    patched_count = text.count(PLATFORM_BLOCK)
    warning_count = text.count(WARNING)
    anchor_count = text.count(PLATFORM_ANCHOR)
    if patched_count == 1 and warning_count == 1 and anchor_count == 1:
        updated, state = text, "PATCHED"
    elif patched_count == 0 and warning_count == 0 and anchor_count == 1:
        updated, state = text.replace(PLATFORM_ANCHOR, PLATFORM_BLOCK, 1), "ORIGINAL"
    else:
        raise SafetyError(
            "Ubuntu 26.04 platform gate: expected one original anchor or one exact patched block, "
            f"got anchor={anchor_count}, patched={patched_count}, warning={warning_count}"
        )
    if "SKIP_PLATFORM_CHECK=" in updated:
        raise SafetyError("platform check unexpectedly assigns SKIP_PLATFORM_CHECK")
    return updated, state, [f"ubuntu26_gate={state.lower()}"]


def transform_shebang(text: str, identity: str, name: str) -> tuple[str, str, list[str]]:
    if identity not in text:
        raise SafetyError(f"{name}: Bash-only identity anchor is missing")
    lines = text.splitlines(keepends=True)
    if not lines:
        raise SafetyError(f"{name}: empty script")
    first = lines[0].rstrip("\r\n")
    ending = lines[0][len(first):] or "\n"
    if re.fullmatch(r"#!/bin/sh\s*", first):
        lines[0] = "#!/bin/bash" + ending
        return "".join(lines), "ORIGINAL", ["bash_shebang=original"]
    if first == "#!/bin/bash":
        return text, "PATCHED", ["bash_shebang=patched"]
    raise SafetyError(f"{name}: unexpected shebang {first!r}")


def transform_spyglass(text: str) -> tuple[str, str, list[str]]:
    return transform_shebang(text, 'if [[ "$1" == *"$id"* ]]; then', "spyglass")


def transform_spyexplain(text: str) -> tuple[str, str, list[str]]:
    return transform_shebang(text, "source `dirname $0`/.platform_check.sh", "spyexplain")


def transform_spyglass_main(text: str) -> tuple[str, str, list[str]]:
    updated, shebang_state, reasons = transform_shebang(text, "ary=($LD_PRELOAD)", "spyglass_main")
    updated, batch_state = replace_component(updated, MAIN_BATCH_OLD, MAIN_BATCH_NEW, "batch system malloc selector")
    updated, gui_state = replace_component(updated, MAIN_GUI_OLD, MAIN_GUI_NEW, "GUI system malloc selector")
    states = (shebang_state, batch_state, gui_state)
    state = "PATCHED" if all(item == "PATCHED" for item in states) else "ORIGINAL" if all(item == "ORIGINAL" for item in states) else "PARTIAL"
    reasons.extend((f"batch_system_malloc={batch_state.lower()}", f"gui_system_malloc={gui_state.lower()}"))
    return updated, state, reasons


TARGETS = (
    TargetSpec("standard-environment", "home:lib/SpyGlass/standard-environment.sh", transform_standard),
    TargetSpec("bundled-perl-wrapper", "install:perl/bin/perl", transform_perl),
    TargetSpec("spygenlib", "home:bin/spygenlib", transform_spygenlib),
    TargetSpec("platform-check", "home:bin/.platform_check.sh", transform_platform, "sh"),
    TargetSpec("spyglass", "home:bin/spyglass", transform_spyglass),
    TargetSpec("spyglass-main", "home:bin/spyglass_main", transform_spyglass_main),
    TargetSpec("spyexplain", "home:bin/spyexplain", transform_spyexplain),
)


def read_os_release(path: Path = Path("/etc/os-release")) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return values
    for line in lines:
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"')
    return values


def host_info(os_release: Path = Path("/etc/os-release")) -> HostInfo:
    release = read_os_release(os_release)
    return HostInfo(platform.machine(), platform.release(), release.get("ID", ""), release.get("VERSION_ID", ""))


def normalize_root(path: Path) -> InstallRoot:
    candidate = path.expanduser().resolve(strict=False)
    if candidate.name == "SPYGLASS_HOME":
        home, install = candidate, candidate.parent
    else:
        install, home = candidate, candidate / "SPYGLASS_HOME"
    if install.name != RELEASE:
        raise SafetyError(f"unsupported install release/path: {install}; expected final component {RELEASE}")
    if not home.is_dir():
        raise SafetyError(f"SPYGLASS_HOME is missing: {home}")
    return InstallRoot(install, home)


def discover_roots(paths: Iterable[str] | None, *, allow_empty: bool = False) -> list[InstallRoot]:
    explicit = list(paths or [])
    candidates = [Path(item) for item in explicit] if explicit else [item for item in DEFAULT_ROOTS if item.exists()]
    roots: list[InstallRoot] = []
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            root = normalize_root(candidate)
        except SafetyError:
            if explicit:
                raise
            continue
        if root.install not in seen:
            seen.add(root.install)
            roots.append(root)
    if not roots and not allow_empty:
        raise SafetyError("no supported SpyGlass X-2025.06 installation roots found")
    return roots


def inspect_target(root: InstallRoot, spec: TargetSpec) -> Inspection:
    path = spec.path_for(root)
    try:
        lst = path.lstat()
    except FileNotFoundError:
        return Inspection(root, spec, path, "MISSING", ["target file is missing"], None, None, None)
    if stat.S_ISLNK(lst.st_mode) or not stat.S_ISREG(lst.st_mode):
        return Inspection(root, spec, path, "UNEXPECTED", ["target must be a regular non-symlink file"], None, None, lst)
    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
        candidate, state, reasons = spec.transform(text)
    except (UnicodeDecodeError, SafetyError) as exc:
        return Inspection(root, spec, path, "UNEXPECTED", [str(exc)], data, None, lst)
    return Inspection(root, spec, path, state, reasons, data, candidate.encode("utf-8"), lst)


def inspect_roots(roots: Iterable[InstallRoot]) -> list[Inspection]:
    return [inspect_target(root, spec) for root in roots for spec in TARGETS]


def inspection_summary(inspections: list[Inspection], host: HostInfo) -> dict:
    roots: dict[str, dict] = {}
    for item in inspections:
        key = str(item.root.install)
        root_result = roots.setdefault(key, {"spyglass_home": str(item.root.home), "targets": [], "library_compiler_payload": (item.root.home / "obj/link.Linux4").exists()})
        target = {"key": item.spec.key, "path": str(item.path), "state": item.state, "reasons": item.reasons}
        if item.before is not None:
            target["sha256"] = sha256_bytes(item.before)
        root_result["targets"].append(target)
    unsafe = any(item.state in {"MISSING", "UNEXPECTED", "UNSUPPORTED_VERSION"} for item in inspections)
    needs = any(item.state in {"ORIGINAL", "PARTIAL"} for item in inspections)
    overall = "UNSUPPORTED" if unsafe or not host.eligible else "NEEDS_PATCH" if needs else "PATCHED"
    return {"schema": 1, "skill": SKILL, "release": RELEASE, "host": dataclasses.asdict(host) | {"eligible": host.eligible}, "overall": overall, "roots": roots}


def print_summary(summary: dict) -> None:
    host = summary["host"]
    print(f"Host: arch={host['arch']} kernel={host['kernel_release']} os={host['os_id']} {host['version_id']} eligible={host['eligible']}")
    print(f"Overall: {summary['overall']}")
    for root, details in summary["roots"].items():
        print(f"\n{root}")
        for target in details["targets"]:
            print(f"  {target['state']:<10} {target['key']:<24} {target['path']}")
            for reason in target["reasons"]:
                print(f"    - {reason}")
        if not details["library_compiler_payload"]:
            print("  NOTE       spygenlib: SPYGLASS_HOME/obj/link.Linux4 is missing; install the Library Compiler payload")


def workspace_tmp(workspace: str | None) -> Path:
    base = Path(workspace).expanduser().resolve() if workspace else Path.cwd().resolve()
    if base == Path("/") or not base.exists() or not base.is_dir():
        raise SafetyError(f"invalid workspace directory: {base}")
    if base == Path("/tmp") or str(base).startswith("/tmp/"):
        raise SafetyError("workspace must not be system /tmp; use the calling workspace and its ./tmp directory")
    temp = base / "tmp" / SKILL
    temp.mkdir(parents=True, exist_ok=True)
    return temp


def new_run_dir(workspace: str | None, operation: str) -> Path:
    parent = workspace_tmp(workspace)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run = parent / f"{operation}-{stamp}-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    run.mkdir(mode=0o700)
    return run


def safe_relative(path: Path) -> Path:
    return Path(*[part.replace(":", "_") for part in path.resolve().parts if part not in ("/", "")])


def fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_bytes_durable(path: Path, data: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(path, mode)
    fsync_dir(path.parent)


def write_json_durable(path: Path, value: dict) -> None:
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    if path.exists():
        with path.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    else:
        write_bytes_durable(path, data, 0o600)
    fsync_dir(path.parent)


def syntax_check(path: Path, shell: str, env: dict[str, str]) -> None:
    binary = shutil.which(shell)
    if not binary:
        raise SafetyError(f"required shell not found: {shell}")
    result = subprocess.run([binary, "-n", str(path)], env=env, capture_output=True, text=True, timeout=30, check=False)
    if result.returncode:
        raise SafetyError(f"syntax check failed for {path}: {result.stderr.strip()}")


def temp_env(run_dir: Path, host: HostInfo, *, system_malloc: bool = False) -> dict[str, str]:
    env = os.environ.copy()
    runtime_tmp = run_dir / "runtime-tmp"
    runtime_tmp.mkdir(parents=True, exist_ok=True)
    for name in ("TMPDIR", "TMP", "TEMP", "SPYGLASS_TMPDIR"):
        env[name] = str(runtime_tmp)
    if system_malloc:
        if not host.eligible:
            raise SafetyError("system malloc compatibility mode is restricted to x86_64 Ubuntu 26.04 with Linux kernel 7")
        env["SPYGLASS_USE_SYSTEM_MALLOC"] = "1"
        env.pop("SPYGLASS_USE_PTMALLOC", None)
        env.pop("SPYGLASS_USE_JEMALLOC", None)
        env.pop("SPYGLASS_USE_TCMALLOC", None)
        env.pop("SPYGLASS_USE_SNPSMEM", None)
    return env


def metadata(item: Inspection) -> dict:
    assert item.file_stat is not None and item.before is not None and item.after is not None
    return {
        "key": item.spec.key,
        "path": str(item.path),
        "root": str(item.root.install),
        "state_before": item.state,
        "state_after": "PATCHED",
        "before_sha256": sha256_bytes(item.before),
        "after_sha256": sha256_bytes(item.after),
        "uid": item.file_stat.st_uid,
        "gid": item.file_stat.st_gid,
        "mode": stat.S_IMODE(item.file_stat.st_mode),
        "mtime_ns": item.file_stat.st_mtime_ns,
    }


def prepare_apply(roots: list[InstallRoot], workspace: str | None, host: HostInfo) -> tuple[Path, Path, dict, list[Inspection]]:
    if not host.eligible:
        raise SafetyError(f"apply is restricted to x86_64 Ubuntu 26.04/Linux 7; detected {host}")
    inspections = inspect_roots(roots)
    unsafe = [item for item in inspections if item.state in {"MISSING", "UNEXPECTED", "UNSUPPORTED_VERSION"}]
    if unsafe:
        detail = "; ".join(f"{item.path}: {', '.join(item.reasons)}" for item in unsafe)
        raise SafetyError(f"preflight refused unknown targets: {detail}")
    run = new_run_dir(workspace, "apply")
    if any(item.path.stat().st_dev != run.stat().st_dev for item in inspections):
        raise SafetyError("workspace ./tmp and all product targets must be on the same filesystem for atomic replacement")
    env = temp_env(run, host)
    targets: list[dict] = []
    for item in inspections:
        assert item.before is not None and item.after is not None and item.file_stat is not None
        relative = safe_relative(item.path)
        backup = run / "backup" / relative
        staged = run / "staged" / relative
        write_bytes_durable(backup, item.before, stat.S_IMODE(item.file_stat.st_mode))
        write_bytes_durable(staged, item.after, stat.S_IMODE(item.file_stat.st_mode))
        os.utime(backup, ns=(item.file_stat.st_atime_ns, item.file_stat.st_mtime_ns))
        os.utime(staged, ns=(item.file_stat.st_atime_ns, item.file_stat.st_mtime_ns))
        syntax_check(staged, item.spec.syntax, env)
        staged_text = staged.read_text(encoding="utf-8")
        _, staged_state, _ = item.spec.transform(staged_text)
        if staged_state != "PATCHED":
            raise SafetyError(f"staged semantic validation failed for {item.path}: {staged_state}")
        entry = metadata(item)
        entry.update({"backup": str(backup), "staged": str(staged), "changed": item.changed})
        targets.append(entry)
    manifest = {
        "schema": 1,
        "skill": SKILL,
        "release": RELEASE,
        "status": "prepared",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "host": dataclasses.asdict(host),
        "run_dir": str(run),
        "targets": targets,
    }
    manifest_path = run / "manifest.json"
    write_json_durable(manifest_path, manifest)
    return run, manifest_path, manifest, inspections


def install_prepared(manifest_path: Path, manifest: dict, inspections: list[Inspection]) -> None:
    by_path = {str(item.path): item for item in inspections}
    changed_entries = [entry for entry in manifest["targets"] if entry["changed"]]
    for entry in manifest["targets"]:
        path = Path(entry["path"])
        if sha256_file(path) != entry["before_sha256"]:
            raise SafetyError(f"target drifted after preflight: {path}")
        if sha256_file(Path(entry["backup"])) != entry["before_sha256"]:
            raise SafetyError(f"backup integrity failure: {entry['backup']}")
        if sha256_file(Path(entry["staged"])) != entry["after_sha256"]:
            raise SafetyError(f"staged integrity failure: {entry['staged']}")
    manifest["status"] = "committing"
    write_json_durable(manifest_path, manifest)
    installed: list[dict] = []
    try:
        for entry in changed_entries:
            path = Path(entry["path"])
            staged = Path(entry["staged"])
            os.chmod(staged, entry["mode"])
            os.chown(staged, entry["uid"], entry["gid"])
            os.replace(staged, path)
            installed.append(entry)
            os.utime(path, ns=(path.stat().st_atime_ns, entry["mtime_ns"]))
            fsync_file(path)
            fsync_dir(path.parent)
            if sha256_file(path) != entry["after_sha256"]:
                raise SafetyError(f"post-install hash mismatch: {path}")
    except Exception:
        for entry in reversed(installed):
            path = Path(entry["path"])
            restore = Path(manifest["run_dir"]) / "recovery" / safe_relative(path)
            backup = Path(entry["backup"])
            write_bytes_durable(restore, backup.read_bytes(), entry["mode"])
            os.chown(restore, entry["uid"], entry["gid"])
            os.replace(restore, path)
            os.utime(path, ns=(path.stat().st_atime_ns, entry["mtime_ns"]))
            fsync_file(path)
            fsync_dir(path.parent)
        manifest["status"] = "restored_after_failure"
        write_json_durable(manifest_path, manifest)
        raise
    manifest["status"] = "committed"
    manifest["committed_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    write_json_durable(manifest_path, manifest)


def load_manifest(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SafetyError(f"cannot read manifest {path}: {exc}") from exc
    if value.get("schema") != 1 or value.get("skill") != SKILL or value.get("release") != RELEASE:
        raise SafetyError("manifest schema/skill/release mismatch")
    return value


def rollback_manifest(manifest_path: Path, manifest: dict) -> None:
    if manifest.get("status") != "committed":
        raise SafetyError(f"rollback requires committed manifest, got {manifest.get('status')}")
    for entry in manifest["targets"]:
        path, backup = Path(entry["path"]), Path(entry["backup"])
        if sha256_file(backup) != entry["before_sha256"]:
            raise SafetyError(f"backup integrity failure: {backup}")
        if sha256_file(path) != entry["after_sha256"]:
            raise SafetyError(f"refusing to overwrite post-apply drift: {path}")
        if path.stat().st_dev != backup.stat().st_dev:
            raise SafetyError(f"backup and target are on different filesystems: {path}")
    restored: list[dict] = []
    for entry in manifest["targets"]:
        if entry["before_sha256"] == entry["after_sha256"]:
            continue
        path, backup = Path(entry["path"]), Path(entry["backup"])
        candidate = Path(manifest["run_dir"]) / "rollback" / safe_relative(path)
        write_bytes_durable(candidate, backup.read_bytes(), entry["mode"])
        os.chown(candidate, entry["uid"], entry["gid"])
        os.replace(candidate, path)
        os.utime(path, ns=(path.stat().st_atime_ns, entry["mtime_ns"]))
        fsync_file(path)
        fsync_dir(path.parent)
        if sha256_file(path) != entry["before_sha256"]:
            raise SafetyError(f"rollback hash mismatch: {path}")
        restored.append(entry)
    manifest["status"] = "rolled_back"
    manifest["rolled_back_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    write_json_durable(manifest_path, manifest)


def run_command(name: str, argv: list[str], cwd: Path, env: dict[str, str], log: Path, timeout: int, required: str | None = None) -> dict:
    started = dt.datetime.now(dt.timezone.utc)
    process = subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        output = stdout + stderr
        code, timed_out = process.returncode, False
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate()
        output, code = stdout + stderr, 124
    log.write_text(output, encoding="utf-8")
    crash = bool(re.search(r"SIG(?:SEGV|ABRT)|Terminator Signal:\s*(?:6|11)\b|Caught signal\s*:\s*(?:6|11)\b", output, re.I))
    marker_ok = required is None or required in output
    return {
        "name": name,
        "argv": argv,
        "exit_code": code,
        "timed_out": timed_out,
        "crash_signal_6_or_11": crash,
        "required_marker": required,
        "marker_ok": marker_ok,
        "ok": code == 0 and not crash and marker_ok,
        "log": str(log),
        "started_at": started.isoformat(),
    }


def verify_root(root: InstallRoot, run: Path, host: HostInfo, gui_seconds: int, no_gui: bool) -> dict:
    root_run = run / root.install.parent.name
    root_run.mkdir(parents=True, exist_ok=True)
    env = temp_env(root_run, host, system_malloc=True)
    env["SPYGLASS_HOME"] = str(root.home)
    env["PATH"] = str(root.home / "bin") + os.pathsep + env.get("PATH", "")
    results: list[dict] = []
    checks = [
        ("perl-version", [str(root.install / "perl/bin/perl"), "-v"], None, 30),
        ("spyglass-version", [str(root.home / "bin/spyglass"), "-version"], "Version X-2025.06", 60),
    ]
    for name, argv, marker, timeout in checks:
        results.append(run_command(name, argv, root_run, env, root_run / f"{name}.log", timeout, marker))
    tcl = root_run / "normal-exit.tcl"
    tcl.write_text('puts "SPYGLASS_COMPAT_NORMAL_OK"\nexit\n', encoding="utf-8")
    results.append(run_command("sg-shell-normal", [str(root.home / "bin/sg_shell"), "-nl", "-tcl", str(tcl)], root_run, env, root_run / "sg-shell-normal.log", 90, "SPYGLASS_COMPAT_NORMAL_OK"))
    results.append(run_command("spyexplain", [str(root.home / "bin/spyexplain"), "-mixed", "--short_help_only"], root_run, env, root_run / "spyexplain.log", 90))
    examples = root.home / "examples/sg_shell/design_query"
    lib, verilog = examples / "example.lib", examples / "test.v"
    if lib.is_file() and verilog.is_file() and "ufe_optional" in str(root.install):
        compile_tcl = root_run / "compile-example.tcl"
        compile_tcl.write_text(
            'puts "SPYGLASS_COMPAT_COMPILE_START"\nnew_project compat_test -f\n'
            f'read_file -type gateslib {{{lib}}}\nread_file {{{verilog}}}\n'
            'set_option enable_gateslib_autocompile yes\ncompile_design\n'
            'puts "SPYGLASS_COMPAT_COMPILE_OK"\nexit\n', encoding="utf-8")
        results.append(run_command("compile-example", [str(root.home / "bin/sg_shell"), "-nl", "-tcl", str(compile_tcl)], root_run, env, root_run / "compile-example.log", 180, "SPYGLASS_COMPAT_COMPILE_OK"))
    else:
        results.append({"name": "compile-example", "ok": True, "skipped": True, "reason": "optional example inputs are unavailable"})
    if no_gui or not env.get("DISPLAY"):
        results.append({"name": "gui-smoke", "ok": True, "skipped": True, "reason": "GUI disabled or DISPLAY unavailable"})
    else:
        gui = run_command("gui-smoke", [str(root.home / "bin/spyglass")], root_run, env, root_run / "gui-smoke.log", gui_seconds)
        if gui["timed_out"] and not gui["crash_signal_6_or_11"]:
            gui["ok"] = True
            gui["expected_timeout"] = True
        results.append(gui)
    payload = root.home / "obj/link.Linux4"
    results.append({"name": "spygenlib-payload", "ok": True, "skipped": not payload.exists(), "path": str(payload), "reason": None if payload.exists() else "Library Compiler payload is missing; taxonomy patch cannot supply it"})
    return {"root": str(root.install), "results": results, "ok": all(item.get("ok", False) for item in results)}


def command_diagnose(args: argparse.Namespace) -> int:
    host = host_info()
    roots = discover_roots(args.root)
    summary = inspection_summary(inspect_roots(roots), host)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_summary(summary)
    return EXIT_UNSUPPORTED if summary["overall"] == "UNSUPPORTED" else EXIT_NEEDS_PATCH if summary["overall"] == "NEEDS_PATCH" else EXIT_OK


def require_write_flags(args: argparse.Namespace) -> None:
    if not args.yes or not args.write_system:
        raise SafetyError("write operation requires both --yes and --write-system after reviewing exact targets")


def command_apply(args: argparse.Namespace) -> int:
    require_write_flags(args)
    host = host_info()
    roots = discover_roots(args.root)
    _, manifest_path, manifest, inspections = prepare_apply(roots, args.workspace, host)
    print(f"Prepared manifest: {manifest_path}")
    for entry in manifest["targets"]:
        action = "replace" if entry["changed"] else "skip (already patched)"
        print(f"  {action}: {entry['path']}")
    install_prepared(manifest_path, manifest, inspections)
    print(f"Committed compatibility patch. Rollback manifest: {manifest_path}")
    return EXIT_OK


def command_rollback(args: argparse.Namespace) -> int:
    require_write_flags(args)
    path = Path(args.manifest).expanduser().resolve()
    manifest = load_manifest(path)
    rollback_manifest(path, manifest)
    print(f"Rolled back all unchanged-since-apply targets from {path}")
    return EXIT_OK


def command_verify(args: argparse.Namespace) -> int:
    host = host_info()
    if not host.eligible:
        raise SafetyError(f"runtime verification is restricted to x86_64 Ubuntu 26.04/Linux 7; detected {host}")
    roots = discover_roots(args.root)
    inspections = inspect_roots(roots)
    structural = inspection_summary(inspections, host)
    if structural["overall"] != "PATCHED":
        raise SafetyError(f"runtime verification requires all known targets to be PATCHED; diagnosed {structural['overall']}")
    manifest_ref = None
    if args.manifest:
        manifest_path = Path(args.manifest).expanduser().resolve()
        manifest = load_manifest(manifest_path)
        if manifest.get("status") not in {"committed", "rolled_back"}:
            raise SafetyError(f"verification manifest has incomplete status: {manifest.get('status')}")
        manifest_ref = {"path": str(manifest_path), "status": manifest.get("status")}
    run = new_run_dir(args.workspace, "verify")
    reports = [verify_root(root, run, host, args.gui_seconds, args.no_gui) for root in roots]
    report = {
        "schema": 1,
        "skill": SKILL,
        "run_dir": str(run),
        "host": dataclasses.asdict(host),
        "structural": structural,
        "manifest": manifest_ref,
        "roots": reports,
        "ok": all(item["ok"] for item in reports),
    }
    report_path = run / "verification.json"
    write_json_durable(report_path, report)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Verification report: {report_path}")
        for root in reports:
            print(f"\n{root['root']}: {'PASS' if root['ok'] else 'FAIL'}")
            for result in root["results"]:
                status = "SKIP" if result.get("skipped") else "PASS" if result.get("ok") else "FAIL"
                detail = result.get("reason") or result.get("log") or result.get("path", "")
                print(f"  {status:<4} {result['name']}: {detail}")
    return EXIT_OK if report["ok"] else EXIT_TRANSACTION


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    diagnose = sub.add_parser("diagnose", help="inspect supported installations without modifying them")
    diagnose.add_argument("--root", action="append", help="X-2025.06 install root or SPYGLASS_HOME; repeatable")
    diagnose.add_argument("--workspace", help="reserved for CLI symmetry; diagnose creates no artifacts")
    diagnose.add_argument("--json", action="store_true")
    diagnose.set_defaults(func=command_diagnose)
    apply = sub.add_parser("apply", help="transactionally install the compatibility adaptation")
    apply.add_argument("--root", action="append")
    apply.add_argument("--workspace", help="workspace whose ./tmp stores backups, staging, and manifest")
    apply.add_argument("--yes", action="store_true", help="confirm the listed operation")
    apply.add_argument("--write-system", action="store_true", help="authorize writes to product installation files")
    apply.set_defaults(func=command_apply)
    verify = sub.add_parser("verify", help="run independent normal-mode runtime checks")
    verify.add_argument("--root", action="append")
    verify.add_argument("--workspace", help="workspace whose ./tmp stores all runtime outputs")
    verify.add_argument("--manifest", help="optional manifest reference for operator bookkeeping")
    verify.add_argument("--gui-seconds", type=int, default=25)
    verify.add_argument("--no-gui", action="store_true")
    verify.add_argument("--json", action="store_true")
    verify.set_defaults(func=command_verify)
    rollback = sub.add_parser("rollback", help="restore originals from a committed manifest")
    rollback.add_argument("--manifest", required=True)
    rollback.add_argument("--yes", action="store_true")
    rollback.add_argument("--write-system", action="store_true")
    rollback.set_defaults(func=command_rollback)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except SafetyError as exc:
        print(f"SAFETY ERROR: {exc}", file=sys.stderr)
        return EXIT_UNSUPPORTED
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"TRANSACTION ERROR: {exc}", file=sys.stderr)
        return EXIT_TRANSACTION


if __name__ == "__main__":
    raise SystemExit(main())
