#!/usr/bin/python3
import hashlib
import os
from pathlib import Path
import sys
import tempfile

binary = Path('/usr/lib/chatgpt/ChatGPT')
fix = Path.home() / '.local/share/chatgpt-sigchld-fix'
env = os.environ.copy()
flags_path = Path(env.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'chatgpt-flags.conf'
flags = []
if flags_path.is_file():
    flags = [s for line in flags_path.read_text().splitlines() if (s := line.strip()) and not s.startswith('#')]
expected = (fix / 'binary.sha256').read_text().strip()
with binary.open('rb') as stream:
    matches = hashlib.file_digest(stream, 'sha256').hexdigest() == expected
if matches and not env.get('LD_PRELOAD'):
    env['LD_PRELOAD'] = str(fix / 'guard.so')
else:
    print('ChatGPT signal workaround skipped: binary changed or LD_PRELOAD already set.', file=sys.stderr)
workspace = Path((fix / 'workspace-root').read_text().strip())
if not workspace.is_absolute() or not workspace.is_dir():
    raise SystemExit('Repair workspace is missing; update workspace-root to an existing absolute task workspace.')
temp_root = workspace / 'tmp'
temp_root.mkdir(exist_ok=True)
env['TMPDIR'] = tempfile.mkdtemp(prefix='chatgpt-runtime-', dir=temp_root)
os.execve(binary, [str(binary), *flags, *sys.argv[1:]], env)
