#!/usr/bin/env python3
"""Offline behavioral checks. TMPDIR must be explicitly inside the workspace."""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

scripts = Path(__file__).resolve().parent
assert os.environ.get('TMPDIR'), 'Set TMPDIR beneath workspace/tmp before testing'
with tempfile.TemporaryDirectory(prefix='chatgpt-tests-', dir=os.environ['TMPDIR']) as td:
    root = Path(td)
    launcher = root / 'codex-launcher'
    shutil.copyfile(scripts / 'chatgpt-launcher.sh', launcher)
    app = root / 'ChatGPT'
    app.write_text('#!/usr/bin/python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n')
    app.chmod(0o755)
    config = root / 'config'
    config.mkdir()
    env = dict(os.environ, XDG_CONFIG_HOME=str(config))
    def launch(*args):
        return json.loads(subprocess.check_output(['bash', str(launcher), *args], env=env))
    assert launch('a b', '') == ['a b', '']
    payload = f'$(touch {root}/injected)'
    (config / 'chatgpt-flags.conf').write_bytes(
        ('  # comment\r\n\n --foo=a b \r\n' + payload + '\n--last').encode())
    assert launch('--cli', 'x y') == ['--foo=a b', payload, '--last', '--cli', 'x y']
    assert not (root / 'injected').exists()

    # Exercise real hook functions with fixture paths, without touching system policy.
    hook = (scripts / 'chatgpt.install').read_text().replace('/etc/apparmor.d', str(root / 'apparmor'))
    hook_path = root / 'hook'; hook_path.write_text(hook)
    policy = root / 'apparmor'; (policy / 'abi').mkdir(parents=True)
    (policy / 'disable').mkdir()
    (policy / 'chatgpt').touch(); (policy / 'abi/4.0').touch()
    (policy / 'disable/chatgpt').symlink_to('missing')
    shell = f'source "{hook_path}"; aa-enabled() {{ return 0; }}; apparmor_parser() {{ echo called >> "{root}/calls"; }}; post_install'
    subprocess.run(['bash', '-c', shell], check=True)
    assert not (root / 'calls').exists()
    (policy / 'disable/chatgpt').unlink()
    subprocess.run(['bash', '-c', shell], check=True)
    assert (root / 'calls').read_text().strip() == 'called'

    # Minimal real deb, with a mocked HTTPS index. Mismatch must never reach makepkg.
    def tar_bytes(name, data):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w:gz') as tf:
            info = tarfile.TarInfo(name); info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
        return stream.getvalue()
    deb = root / 'test.deb'
    with deb.open('wb') as out:
        out.write(b'!<arch>\n')
        for name, data in [('debian-binary', b'2.0\n'), ('control.tar.gz', tar_bytes('./control', b'Package: chatgpt\nVersion: 1.0\nArchitecture: amd64\n')), ('data.tar.gz', tar_bytes('./placeholder', b'x'))]:
            out.write(f'{name+"/":<16}{0:<12}{0:<6}{0:<6}{"100644":<8}{len(data):<10}`\n'.encode())
            out.write(data)
            if len(data) % 2: out.write(b'\n')
    bins = root / 'bin'; bins.mkdir()
    curl = bins / 'curl'
    curl.write_text('#!/bin/bash\nwhile (( $# )); do if [[ $1 == --output ]]; then cp "$TEST_INDEX" "$2"; exit; fi; shift; done\nexit 1\n')
    curl.chmod(0o755)
    makepkg = bins / 'makepkg'; makepkg.write_text('#!/bin/bash\ntouch "$TEST_MARKER"\nexit 99\n'); makepkg.chmod(0o755)
    index = root / 'index'; marker = root / 'built'
    env.update(PATH=str(bins)+':'+os.environ['PATH'], TEST_INDEX=str(index), TEST_MARKER=str(marker), CHATGPT_ARCH_WORKSPACE=str(root))
    for version, digest, size in [('1.0', '0'*64, deb.stat().st_size), ('2.0', hashlib.sha256(deb.read_bytes()).hexdigest(), deb.stat().st_size), ('1.0', hashlib.sha256(deb.read_bytes()).hexdigest(), deb.stat().st_size+1)]:
        index.write_text(f'Package: chatgpt\nVersion: {version}\nArchitecture: amd64\nFilename: pool/main/c/chatgpt/chatgpt_1.0_amd64.deb\nSHA256: {digest}\nSize: {size}\n\n')
        result = subprocess.run(['bash', str(scripts/'auto-deb-install.sh'), str(deb)], env=env, capture_output=True, text=True)
        assert result.returncode != 0 and 'does not uniquely match' in result.stderr, result.stderr
        assert not marker.exists()
print('PASS: literal flags, argument order, CRLF, no evaluation, AppArmor disabled/enabled, SHA/version/size rejection before build')
