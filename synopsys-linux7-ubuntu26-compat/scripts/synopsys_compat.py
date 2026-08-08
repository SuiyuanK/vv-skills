#!/usr/bin/env python3
"""Transactional Synopsys wrapper compatibility adapter for Ubuntu 26.04/Linux 7."""

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

SKILL = "synopsys-linux7-ubuntu26-compat"
SCHEMA = 1
EXIT_OK = 0
EXIT_NEEDS_PATCH = 2
EXIT_UNSUPPORTED = 3
EXIT_TRANSACTION = 4
DEFAULT_SYNOPSYS_ROOT = Path("/opt/eda/Synopsys")


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
        return (
            self.arch == "x86_64"
            and self.os_id == "ubuntu"
            and self.version_id == "26.04"
            and self.kernel_release.split(".", 1)[0] == "7"
        )


@dataclasses.dataclass(frozen=True)
class TargetSpec:
    key: str
    product: str
    relative: str
    release_component: str
    transform: Callable[[str], tuple[str, str, list[str]]]
    syntax: str

    def path_for(self, root: Path) -> Path:
        return root / self.relative


@dataclasses.dataclass
class Inspection:
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


def host_info(os_release: Path = Path("/etc/os-release")) -> HostInfo:
    release = read_os_release(os_release)
    return HostInfo(platform.machine(), platform.release(), release.get("ID", ""), release.get("VERSION_ID", ""))


def replace_exact(text: str, old: str, new: str, name: str, expected: int = 1) -> tuple[str, str]:
    old_count = text.count(old)
    new_count = text.count(new)
    if old_count == expected and new_count == 0:
        return text.replace(old, new), "ORIGINAL"
    if old_count == 0 and new_count == expected:
        return text, "PATCHED"
    raise SafetyError(f"{name}: expected {expected} original or patched anchors, got old={old_count}, new={new_count}")


def transform_snps_shell(text: str) -> tuple[str, str, list[str]]:
    if not text.startswith("#!/bin/sh") or "real_synopsys_install_root_bin" not in text or "snps_common.sh" not in text:
        raise SafetyError("snps_shell identity anchors are missing")
    pairs = (
        ('if [ T"${real_synopsys_install_root_bin}" == "T" ]; then', 'if [ T"${real_synopsys_install_root_bin}" = "T" ]; then'),
        ('if [ T"${real_platform}" == "T" ] && [ -f "${real_synopsys_install_root_bin}/bin/snps_platform" ] ; then', 'if [ T"${real_platform}" = "T" ] && [ -f "${real_synopsys_install_root_bin}/bin/snps_platform" ] ; then'),
    )
    updated = text
    states: list[str] = []
    for index, (old, new) in enumerate(pairs, 1):
        updated, state = replace_exact(updated, old, new, f"snps_shell POSIX test {index}")
        states.append(state)
    overall = "PATCHED" if all(s == "PATCHED" for s in states) else "ORIGINAL" if all(s == "ORIGINAL" for s in states) else "PARTIAL"
    return updated, overall, [f"posix_test_{i + 1}={s.lower()}" for i, s in enumerate(states)]


def replace_shebang(text: str, original: str, patched: str, name: str, identities: Iterable[str]) -> tuple[str, str, list[str]]:
    missing = [anchor for anchor in identities if anchor not in text]
    if missing:
        raise SafetyError(f"{name}: identity anchors are missing: {missing!r}")
    lines = text.splitlines(keepends=True)
    if not lines:
        raise SafetyError(f"{name}: empty script")
    first = lines[0].rstrip("\r\n")
    ending = lines[0][len(first):] or "\n"
    original_count = sum(line.rstrip("\r\n") == original for line in lines)
    patched_count = sum(line.rstrip("\r\n") == patched for line in lines)
    if first == original and original_count == 1 and patched_count == 0:
        lines[0] = patched + ending
        return "".join(lines), "ORIGINAL", ["bash_shebang=original"]
    if first == patched and original_count == 0 and patched_count == 1:
        return text, "PATCHED", ["bash_shebang=patched"]
    if first in {original, patched}:
        raise SafetyError(
            f"{name}: expected one original or patched shebang, "
            f"got original={original_count}, patched={patched_count}"
        )
    raise SafetyError(f"{name}: unexpected shebang {first!r}")


def transform_icc2(text: str) -> tuple[str, str, list[str]]:
    return replace_shebang(text, "#!/bin/sh", "#!/bin/bash", "icc2_shell", ('if [[ "$VS" =~ "11" ]]', "if [ $OS_Version == 1 ]"))


def transform_vcs(text: str) -> tuple[str, str, list[str]]:
    return replace_shebang(text, "#!/bin/sh -h", "#!/bin/bash -h", "vcs", ("function create_euclide_db()", "declare -a POST_SCRIPTS", 'if [[ -v EUCLIDE_HOME ]]'))


def transform_verdi(text: str) -> tuple[str, str, list[str]]:
    return replace_shebang(text, "#!/bin/sh", "#!/bin/bash", "Verdi .wrapper", ('original_argv=("$@")', "while [[ $# -gt 0 ]]", "source ${interactive_debug_file_eman}"))


TARGETS = (
    TargetSpec("dc-snps-shell", "dc", "syn/V-2023.12-SP3/bin/snps_shell", "V-2023.12-SP3", transform_snps_shell, "dash"),
    TargetSpec("lc-snps-shell", "lc", "lc/V-2023.12-SP3/bin/snps_shell", "V-2023.12-SP3", transform_snps_shell, "dash"),
    TargetSpec("icc2-shell", "icc2", "syn/V-2023.12-SP3/icc2/bin/icc2_shell", "V-2023.12-SP3", transform_icc2, "bash"),
    TargetSpec("vcs", "vcs", "vcs/W-2024.09-SP1/bin/vcs", "W-2024.09-SP1", transform_vcs, "bash"),
    TargetSpec("verdi-wrapper", "verdi", "verdi/W-2024.09-SP1/bin/.wrapper", "W-2024.09-SP1", transform_verdi, "bash"),
)

KNOWN_BINARIES = {
    "scl": ("scl/2024.06/linux64/bin/sclsh", ("libncurses.so.5", "libtinfo.so.5")),
    "dc": ("syn/V-2023.12-SP3/linux64/syn/bin/common_shell_exec", ("libpython3.6m.so.1.0", "libpng12.so.0")),
    "lc": ("lc/V-2023.12-SP3/linux64/lc/bin/lc_shell_exec", ("libncurses.so.5", "libtinfo.so.5", "libpng12.so.0")),
    "icc2": ("syn/V-2023.12-SP3/icc2/linux64/nwtn/bin/icc2_exec", ("libtinfo.so.5", "libpython3.6m.so.1.0", "libsasl2.so.3")),
    "verdi": ("verdi/W-2024.09-SP1/platform/linux64/bin/Novas", ("libxml2.so.2", "libpng12.so.0")),
}


def validate_root(root: Path) -> Path:
    root = root.expanduser().resolve(strict=False)
    if root.name != "Synopsys" or not root.is_dir():
        raise SafetyError(f"expected existing Synopsys root, got {root}")
    for spec in TARGETS:
        if spec.release_component not in Path(spec.relative).parts:
            raise SafetyError(f"internal target release mismatch: {spec.key}")
    return root


def candidate_syntax_error(text: str, shell: str) -> str | None:
    binary = shutil.which(shell)
    if not binary:
        return f"required syntax checker is missing: {shell}"
    try:
        result = subprocess.run(
            [binary, "-n"],
            input=text,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return f"{shell} syntax check could not run: {exc}"
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        return f"{shell} candidate syntax check failed: {detail}"
    return None


def inspect_target(root: Path, spec: TargetSpec) -> Inspection:
    path = spec.path_for(root)
    try:
        lst = path.lstat()
    except FileNotFoundError:
        return Inspection(spec, path, "MISSING", ["target file is missing"], None, None, None)
    if stat.S_ISLNK(lst.st_mode) or not stat.S_ISREG(lst.st_mode):
        return Inspection(spec, path, "UNEXPECTED", ["target must be a regular non-symlink file"], None, None, lst)
    data = path.read_bytes()
    try:
        candidate, state, reasons = spec.transform(data.decode("utf-8"))
    except (UnicodeDecodeError, SafetyError) as exc:
        return Inspection(spec, path, "UNEXPECTED", [str(exc)], data, None, lst)
    syntax_error = candidate_syntax_error(candidate, spec.syntax)
    if syntax_error:
        return Inspection(spec, path, "BLOCKED_VENDOR_SCRIPT", reasons + [syntax_error], data, candidate.encode(), lst)
    return Inspection(spec, path, state, reasons, data, candidate.encode(), lst)


def inspect_targets(root: Path, products: set[str] | None = None) -> list[Inspection]:
    return [inspect_target(root, spec) for spec in TARGETS if products is None or spec.product in products]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def elf_metadata(path: Path) -> dict | None:
    readelf = shutil.which("readelf")
    if not readelf or not path.is_file():
        return None
    tool_env = os.environ.copy()
    tool_env.update({"LC_ALL": "C", "LANG": "C"})
    try:
        header = subprocess.run(
            [readelf, "-h", str(path)], env=tool_env, capture_output=True, text=True, timeout=30, check=False
        )
        dynamic = subprocess.run(
            [readelf, "-d", str(path)], env=tool_env, capture_output=True, text=True, timeout=30, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if header.returncode or dynamic.returncode:
        return None
    elf_class = re.search(r"^\s*Class:\s*(\S+)", header.stdout, re.MULTILINE)
    machine = re.search(r"^\s*Machine:\s*(.+?)\s*$", header.stdout, re.MULTILINE)
    soname = re.search(r"\(SONAME\).*\[([^]]+)\]", dynamic.stdout)
    needed = re.findall(r"\(NEEDED\).*\[([^]]+)\]", dynamic.stdout)
    return {
        "class": elf_class.group(1) if elf_class else None,
        "machine": machine.group(1) if machine else None,
        "soname": soname.group(1) if soname else None,
        "needed": needed,
    }


def is_x86_64_elf(value: dict | None) -> bool:
    if not value or value.get("class") != "ELF64":
        return False
    machine = str(value.get("machine") or "").lower()
    return machine in {"advanced micro devices x86-64", "amd x86-64", "x86-64"}


def elf_soname(path: Path) -> str | None:
    value = elf_metadata(path)
    return value.get("soname") if value else None


def candidate_product(root: Path, path: Path) -> str | None:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return None
    if not parts:
        return None
    if parts[0] == "scl":
        return "scl"
    if parts[0] == "lc":
        return "lc"
    if parts[0] == "syn":
        return "icc2" if "icc2" in parts else "dc"
    if parts[0] == "vcs":
        return "vcs"
    if parts[0] in {"verdi", "verdi_supp"}:
        return "verdi"
    return None


def runtime_dependency_report(root: Path) -> dict[str, dict]:
    report: dict[str, dict] = {}
    for product, (relative, required) in KNOWN_BINARIES.items():
        binary = root / relative
        item = {"binary": str(binary), "exists": binary.is_file(), "required_legacy": [], "status": "MISSING_BINARY"}
        if binary.is_file():
            item["status"] = "BLOCKED_DEPENDENCY"
            for name in required:
                candidates: list[dict] = []
                for candidate in root.glob(f"**/{name}*"):
                    if not candidate.is_file() or candidate.is_symlink():
                        continue
                    elf = elf_metadata(candidate)
                    if not is_x86_64_elf(elf):
                        continue
                    assert elf is not None
                    source_product = candidate_product(root, candidate)
                    candidates.append(
                        {
                            "path": str(candidate),
                            "source_product": source_product,
                            "same_product": source_product == product,
                            "elf_class": elf["class"],
                            "machine": elf["machine"],
                            "soname": elf["soname"],
                            "needed": elf["needed"],
                            "exact_soname": elf["soname"] == name,
                        }
                    )
                item["required_legacy"].append({"name": name, "synopsys_candidates": candidates})
            if all(
                any(c["exact_soname"] and c["same_product"] for c in dep["synopsys_candidates"])
                for dep in item["required_legacy"]
            ):
                item["status"] = "SAME_PRODUCT_CANDIDATES_UNVALIDATED"
            elif any(
                any(c["exact_soname"] and c["same_product"] for c in dep["synopsys_candidates"])
                for dep in item["required_legacy"]
            ):
                item["status"] = "PARTIAL_SAME_PRODUCT_CANDIDATES"
        report[product] = item
    return report


def supplement_report(root: Path) -> dict:
    supp = root / "verdi_supp/W-2024.09-SP1"
    verdi = root / "verdi/W-2024.09-SP1"
    post = supp / "etc/post_install.sh"
    return {
        "supplement": str(supp),
        "main_verdi": str(verdi),
        "same_release": supp.name == verdi.name == "W-2024.09-SP1",
        "post_install_exists": post.is_file(),
        "status": "REQUIRES_VALIDATED_INTEGRATION" if supp.is_dir() and verdi.is_dir() else "MISSING",
        "automatic_move": False,
    }


def summary(root: Path, host: HostInfo) -> dict:
    inspections = inspect_targets(root)
    unsafe = any(i.state in {"MISSING", "UNEXPECTED"} for i in inspections)
    blocked = any(i.state == "BLOCKED_VENDOR_SCRIPT" for i in inspections)
    needs = any(i.state in {"ORIGINAL", "PARTIAL"} for i in inspections)
    if unsafe or not host.eligible:
        overall = "UNSUPPORTED"
    elif blocked:
        overall = "PARTIALLY_BLOCKED"
    elif needs:
        overall = "NEEDS_PATCH"
    else:
        overall = "PATCHED"
    return {
        "schema": SCHEMA,
        "skill": SKILL,
        "host": dataclasses.asdict(host) | {"eligible": host.eligible},
        "synopsys_root": str(root),
        "overall": overall,
        "targets": [
            {
                "key": i.spec.key,
                "product": i.spec.product,
                "path": str(i.path),
                "state": i.state,
                "reasons": i.reasons,
                **({"sha256": sha256_bytes(i.before)} if i.before is not None else {}),
            }
            for i in inspections
        ],
        "runtime_dependencies": runtime_dependency_report(root),
        "verdi_supp": supplement_report(root),
        "notes": [
            "SCL license-server core is intentionally unchanged.",
            "No Xilinx library is accepted as a Synopsys runtime dependency source.",
            "No global LD_LIBRARY_PATH or system library path is modified.",
        ],
    }


def print_summary(value: dict) -> None:
    host = value["host"]
    print(f"Host: {host['arch']} {host['os_id']} {host['version_id']} kernel={host['kernel_release']} eligible={host['eligible']}")
    print(f"Overall wrappers: {value['overall']}")
    for target in value["targets"]:
        print(f"  {target['state']:<10} {target['key']:<20} {target['path']}")
        for reason in target["reasons"]:
            print(f"    - {reason}")
    print("Runtime dependency status:")
    for product, item in value["runtime_dependencies"].items():
        print(f"  {item['status']:<30} {product}: {item['binary']}")
        for dep in item.get("required_legacy", []):
            same = [c["path"] for c in dep["synopsys_candidates"] if c["exact_soname"] and c["same_product"]]
            cross = [c["path"] for c in dep["synopsys_candidates"] if c["exact_soname"] and not c["same_product"]]
            if same:
                detail = ", ".join(same)
            elif cross:
                detail = "cross-product clues only: " + ", ".join(cross)
            else:
                detail = "no exact Synopsys x86-64 SONAME candidate"
            print(f"    - {dep['name']}: {detail}")
    print(f"Verdi supplement: {value['verdi_supp']['status']} (automatic move disabled)")


def workspace_tmp(workspace: str | None) -> Path:
    base = Path(workspace).expanduser().resolve() if workspace else Path.cwd().resolve()
    if base == Path("/") or not base.is_dir() or base == Path("/tmp") or str(base).startswith("/tmp/"):
        raise SafetyError(f"workspace must be an existing non-system directory, got {base}")
    result = base / "tmp" / SKILL
    result.mkdir(parents=True, exist_ok=True)
    return result


def new_run(workspace: str | None, operation: str) -> Path:
    parent = workspace_tmp(workspace)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run = parent / f"{operation}-{stamp}-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    run.mkdir(mode=0o700)
    return run


def temp_env(run: Path) -> dict[str, str]:
    runtime = run / "runtime-tmp"
    runtime.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    for key in ("TMPDIR", "TMP", "TEMP"):
        env[key] = str(runtime)
    return env


def safe_relative(path: Path) -> Path:
    return Path(*[part.replace(":", "_") for part in path.resolve().parts if part not in ("", "/")])


def fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_bytes(path: Path, data: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(path, mode)
    fsync_dir(path.parent)


def write_json(path: Path, value: dict) -> None:
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    if path.exists():
        with path.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    else:
        write_bytes(path, data, 0o600)
    fsync_dir(path.parent)


def get_xattrs(path: Path) -> dict[str, str]:
    try:
        return {name: os.getxattr(path, name).hex() for name in os.listxattr(path)}
    except OSError:
        return {}


def set_xattrs(path: Path, values: dict[str, str]) -> None:
    for name, value in values.items():
        os.setxattr(path, name, bytes.fromhex(value))


def syntax_check(path: Path, shell: str, env: dict[str, str]) -> None:
    binary = shutil.which(shell)
    if not binary:
        raise SafetyError(f"required syntax checker is missing: {shell}")
    result = subprocess.run([binary, "-n", str(path)], env=env, capture_output=True, text=True, timeout=60, check=False)
    if result.returncode:
        raise SafetyError(f"{shell} syntax check failed for {path}: {result.stderr.strip()}")


def metadata(item: Inspection) -> dict:
    assert item.before is not None and item.after is not None and item.file_stat is not None
    return {
        "key": item.spec.key,
        "product": item.spec.product,
        "path": str(item.path),
        "state_before": item.state,
        "before_sha256": sha256_bytes(item.before),
        "after_sha256": sha256_bytes(item.after),
        "uid": item.file_stat.st_uid,
        "gid": item.file_stat.st_gid,
        "mode": stat.S_IMODE(item.file_stat.st_mode),
        "atime_ns": item.file_stat.st_atime_ns,
        "mtime_ns": item.file_stat.st_mtime_ns,
        "xattrs": get_xattrs(item.path),
        "changed": item.changed,
    }


def prepare(
    root: Path,
    workspace: str | None,
    host: HostInfo,
    products: set[str] | None = None,
) -> tuple[Path, Path, dict, list[Inspection]]:
    if not host.eligible:
        raise SafetyError(f"writes are restricted to x86_64 Ubuntu 26.04/Linux 7; detected {host}")
    all_inspections = inspect_targets(root)
    selected = [i for i in all_inspections if products is None or i.spec.product in products]
    if not selected:
        raise SafetyError("no wrapper targets selected")
    unsafe = [i for i in selected if i.state in {"MISSING", "UNEXPECTED", "BLOCKED_VENDOR_SCRIPT"}]
    if unsafe:
        raise SafetyError("preflight refused targets: " + "; ".join(f"{i.path}: {', '.join(i.reasons)}" for i in unsafe))
    inspections = selected
    run = new_run(workspace, "apply")
    if any(i.path.stat().st_dev != run.stat().st_dev for i in inspections):
        raise SafetyError("workspace ./tmp and product targets must share a filesystem for atomic replacement")
    env = temp_env(run)
    entries: list[dict] = []
    for item in inspections:
        assert item.before is not None and item.after is not None and item.file_stat is not None
        relative = safe_relative(item.path)
        backup = run / "backup" / relative
        staged = run / "staged" / relative
        mode = stat.S_IMODE(item.file_stat.st_mode)
        write_bytes(backup, item.before, mode)
        write_bytes(staged, item.after, mode)
        os.utime(backup, ns=(item.file_stat.st_atime_ns, item.file_stat.st_mtime_ns))
        os.utime(staged, ns=(item.file_stat.st_atime_ns, item.file_stat.st_mtime_ns))
        syntax_check(staged, item.spec.syntax, env)
        _, staged_state, _ = item.spec.transform(staged.read_text(encoding="utf-8"))
        if staged_state != "PATCHED":
            raise SafetyError(f"staged semantic validation failed: {item.path}: {staged_state}")
        entry = metadata(item)
        entry.update({"backup": str(backup), "staged": str(staged)})
        entries.append(entry)
    manifest = {
        "schema": SCHEMA,
        "skill": SKILL,
        "status": "prepared",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "host": dataclasses.asdict(host),
        "synopsys_root": str(root),
        "products": sorted({item.spec.product for item in inspections}),
        "run_dir": str(run),
        "targets": entries,
    }
    manifest_path = run / "manifest.json"
    write_json(manifest_path, manifest)
    return run, manifest_path, manifest, inspections


def install(manifest_path: Path, manifest: dict) -> None:
    for entry in manifest["targets"]:
        path = Path(entry["path"])
        if sha256_file(path) != entry["before_sha256"]:
            raise SafetyError(f"target drifted after preflight: {path}")
        if sha256_file(Path(entry["backup"])) != entry["before_sha256"]:
            raise SafetyError(f"backup integrity failure: {entry['backup']}")
        if sha256_file(Path(entry["staged"])) != entry["after_sha256"]:
            raise SafetyError(f"staged integrity failure: {entry['staged']}")
    manifest["status"] = "committing"
    write_json(manifest_path, manifest)
    installed: list[dict] = []
    try:
        for entry in manifest["targets"]:
            if not entry["changed"]:
                continue
            path = Path(entry["path"])
            staged = Path(entry["staged"])
            os.chmod(staged, entry["mode"])
            os.chown(staged, entry["uid"], entry["gid"])
            set_xattrs(staged, entry["xattrs"])
            os.replace(staged, path)
            installed.append(entry)
            os.utime(path, ns=(entry["atime_ns"], entry["mtime_ns"]))
            fsync_file(path)
            fsync_dir(path.parent)
            if sha256_file(path) != entry["after_sha256"]:
                raise SafetyError(f"post-install hash mismatch: {path}")
    except Exception:
        for entry in reversed(installed):
            path = Path(entry["path"])
            recovery = Path(manifest["run_dir"]) / "recovery" / safe_relative(path)
            write_bytes(recovery, Path(entry["backup"]).read_bytes(), entry["mode"])
            os.chown(recovery, entry["uid"], entry["gid"])
            set_xattrs(recovery, entry["xattrs"])
            os.replace(recovery, path)
            os.utime(path, ns=(entry["atime_ns"], entry["mtime_ns"]))
            fsync_file(path)
            fsync_dir(path.parent)
        manifest["status"] = "restored_after_failure"
        write_json(manifest_path, manifest)
        raise
    manifest["status"] = "committed"
    manifest["committed_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    write_json(manifest_path, manifest)


def load_manifest(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SafetyError(f"cannot load manifest {path}: {exc}") from exc
    if value.get("schema") != SCHEMA or value.get("skill") != SKILL:
        raise SafetyError("manifest schema/skill mismatch")
    return value


def rollback(manifest_path: Path, manifest: dict) -> None:
    if manifest.get("status") != "committed":
        raise SafetyError(f"rollback requires committed manifest, got {manifest.get('status')}")
    for entry in manifest["targets"]:
        path, backup = Path(entry["path"]), Path(entry["backup"])
        if sha256_file(backup) != entry["before_sha256"]:
            raise SafetyError(f"backup integrity failure: {backup}")
        if sha256_file(path) != entry["after_sha256"]:
            raise SafetyError(f"refusing to overwrite post-apply drift: {path}")
        if path.stat().st_dev != backup.stat().st_dev:
            raise SafetyError(f"backup and target filesystems differ: {path}")
    for entry in manifest["targets"]:
        if not entry["changed"]:
            continue
        path = Path(entry["path"])
        candidate = Path(manifest["run_dir"]) / "rollback" / safe_relative(path)
        write_bytes(candidate, Path(entry["backup"]).read_bytes(), entry["mode"])
        os.chown(candidate, entry["uid"], entry["gid"])
        set_xattrs(candidate, entry["xattrs"])
        os.replace(candidate, path)
        os.utime(path, ns=(entry["atime_ns"], entry["mtime_ns"]))
        fsync_file(path)
        fsync_dir(path.parent)
    manifest["status"] = "rolled_back"
    manifest["rolled_back_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    write_json(manifest_path, manifest)


def run_command(name: str, argv: list[str], cwd: Path, env: dict[str, str], timeout: int) -> dict:
    log = cwd / f"{name}.log"
    process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        code = process.returncode
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
        code = 124
    output = stdout + stderr
    log.write_text(output, encoding="utf-8")
    crash = bool(re.search(r"SIG(?:SEGV|ABRT)|signal\s*[:=]?\s*(?:6|11)\b", output, re.I))
    loader = bool(re.search(r"error while loading shared libraries|cannot open shared object file", output, re.I))
    return {"name": name, "argv": argv, "exit_code": code, "timed_out": timed_out, "crash": crash, "loader_error": loader, "ok": code == 0 and not crash and not loader, "log": str(log)}


def verify(
    root: Path,
    workspace: str | None,
    no_runtime: bool,
    products: set[str] | None = None,
) -> tuple[dict, Path]:
    inspections = inspect_targets(root, products)
    if not inspections:
        raise SafetyError("no wrapper targets selected")
    if any(i.state != "PATCHED" for i in inspections):
        raise SafetyError("verify requires every selected wrapper target to be PATCHED")
    run = new_run(workspace, "verify")
    env = temp_env(run)
    results: list[dict] = []
    for item in inspections:
        staged = item.path
        syntax_check(staged, item.spec.syntax, env)
        results.append({"name": f"syntax-{item.spec.key}", "ok": True, "path": str(staged)})
    if not no_runtime:
        env.update({"SNPSLMD_LICENSE_FILE": os.environ.get("SNPSLMD_LICENSE_FILE", "27000@vv-ubuntu")})
        probes = {
            "lc": ("lc-version", [str(root / "lc/V-2023.12-SP3/bin/lc_shell"), "-version"]),
            "dc": ("dc-version", [str(root / "syn/V-2023.12-SP3/bin/dc_shell"), "-version"]),
            "icc2": ("icc2-version", [str(root / "syn/V-2023.12-SP3/icc2/bin/icc2_shell"), "-version"]),
            "vcs": ("vcs-id", [str(root / "vcs/W-2024.09-SP1/bin/vcs"), "-id"]),
            "verdi": ("verdi-id", [str(root / "verdi/W-2024.09-SP1/bin/verdi"), "-id"]),
        }
        for product, (name, argv) in probes.items():
            if products is None or product in products:
                results.append(run_command(name, argv, run, env, 90))
    report = {
        "schema": SCHEMA,
        "skill": SKILL,
        "run_dir": str(run),
        "products": sorted({item.spec.product for item in inspections}),
        "runtime_skipped": no_runtime,
        "results": results,
        "runtime_dependencies": runtime_dependency_report(root),
        "ok": all(item["ok"] for item in results),
    }
    path = run / "verification.json"
    write_json(path, report)
    return report, path


def require_write(args: argparse.Namespace) -> None:
    if not args.yes or not args.write_system:
        raise SafetyError("write operation requires both --yes and --write-system")


def command_inspect(args: argparse.Namespace) -> int:
    root = validate_root(Path(args.synopsys_root))
    value = summary(root, host_info())
    print(json.dumps(value, indent=2, sort_keys=True) if args.json else "", end="" if args.json else "")
    if not args.json:
        print_summary(value)
    if value["overall"] == "UNSUPPORTED":
        return EXIT_UNSUPPORTED
    if value["overall"] in {"NEEDS_PATCH", "PARTIALLY_BLOCKED"}:
        return EXIT_NEEDS_PATCH
    return EXIT_OK


def selected_products(args: argparse.Namespace) -> set[str] | None:
    values = getattr(args, "product", None)
    return set(values) if values else None


def command_prepare(args: argparse.Namespace) -> int:
    root = validate_root(Path(args.synopsys_root))
    _, path, manifest, _ = prepare(root, args.workspace, host_info(), selected_products(args))
    print(f"Prepared manifest: {path}")
    for entry in manifest["targets"]:
        print(f"  {'replace' if entry['changed'] else 'skip'}: {entry['path']}")
    return EXIT_OK


def command_apply(args: argparse.Namespace) -> int:
    require_write(args)
    root = validate_root(Path(args.synopsys_root))
    _, path, manifest, _ = prepare(root, args.workspace, host_info(), selected_products(args))
    print(f"Prepared manifest: {path}")
    install(path, manifest)
    print(f"Committed wrapper adaptation. Rollback manifest: {path}")
    return EXIT_OK


def command_verify(args: argparse.Namespace) -> int:
    root = validate_root(Path(args.synopsys_root))
    report, path = verify(root, args.workspace, args.no_runtime, selected_products(args))
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else f"Verification report: {path}\nOverall: {'PASS' if report['ok'] else 'FAIL'}")
    return EXIT_OK if report["ok"] else EXIT_TRANSACTION


def command_rollback(args: argparse.Namespace) -> int:
    require_write(args)
    path = Path(args.manifest).expanduser().resolve()
    rollback(path, load_manifest(path))
    print(f"Rolled back unchanged-since-apply targets from {path}")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "diagnose"):
        item = sub.add_parser(name, help="inspect supported Synopsys installations without writes")
        item.add_argument("--synopsys-root", default=str(DEFAULT_SYNOPSYS_ROOT))
        item.add_argument("--json", action="store_true")
        item.set_defaults(func=command_inspect)
    prep = sub.add_parser("prepare", help="stage and validate wrapper candidates without product writes")
    prep.add_argument("--synopsys-root", default=str(DEFAULT_SYNOPSYS_ROOT))
    prep.add_argument("--workspace")
    prep.add_argument("--product", action="append", choices=sorted({spec.product for spec in TARGETS}), help="stage only this product; repeat to select several")
    prep.set_defaults(func=command_prepare)
    apply = sub.add_parser("apply", help="prepare and atomically install wrapper adaptations")
    apply.add_argument("--synopsys-root", default=str(DEFAULT_SYNOPSYS_ROOT))
    apply.add_argument("--workspace")
    apply.add_argument("--product", action="append", choices=sorted({spec.product for spec in TARGETS}), help="apply only this product; repeat to select several")
    apply.add_argument("--yes", action="store_true")
    apply.add_argument("--write-system", action="store_true")
    apply.set_defaults(func=command_apply)
    check = sub.add_parser("verify", help="verify syntax and optionally run safe runtime probes")
    check.add_argument("--synopsys-root", default=str(DEFAULT_SYNOPSYS_ROOT))
    check.add_argument("--workspace")
    check.add_argument("--product", action="append", choices=sorted({spec.product for spec in TARGETS}), help="verify only this product; repeat to select several")
    check.add_argument("--no-runtime", action="store_true")
    check.add_argument("--json", action="store_true")
    check.set_defaults(func=command_verify)
    undo = sub.add_parser("rollback", help="restore originals from a committed manifest")
    undo.add_argument("--manifest", required=True)
    undo.add_argument("--yes", action="store_true")
    undo.add_argument("--write-system", action="store_true")
    undo.set_defaults(func=command_rollback)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
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
