#!/usr/bin/env python3
"""Build and validate Bibata SVG companions; never install or change settings."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib
import xml.etree.ElementTree as ET

REQUIRED = '''default context-menu help pointer progress wait cell crosshair text
vertical-text alias copy move no-drop not-allowed grab grabbing all-scroll
col-resize row-resize n-resize e-resize s-resize w-resize ne-resize nw-resize
se-resize sw-resize ew-resize ns-resize nesw-resize nwse-resize zoom-in zoom-out
dnd-ask all-resize'''.split()
VARIANTS = ['Bibata-Modern-Classic', 'Bibata-Modern-Ice', 'Bibata-Modern-Amber']


def build(args: argparse.Namespace) -> Path:
    source = args.source_root.resolve(strict=True)
    legacy = args.legacy_theme.resolve(strict=True)
    config = tomllib.loads((source / 'configs/normal/x.build.toml').read_text())['cursors']
    fallback = config.pop('fallback_settings')
    render = json.loads((source / 'render.json').read_text())[args.variant]
    svg_dir = source / render['dir']
    renderer = shutil.which('rsvg-convert')
    if not renderer:
        raise ValueError('rsvg-convert missing: install librsvg only with user authorization')
    if not re.fullmatch('[0-9a-f]{40}', args.commit):
        raise ValueError('--commit must be a full lowercase SHA-1')
    if legacy.name != args.variant:
        raise ValueError('--legacy-theme basename must match --variant')
    cursors = legacy / 'cursors'
    if not (cursors / 'default').is_file():
        raise ValueError('Legacy default cursor is missing')
    for p in cursors.iterdir():
        if not p.resolve(strict=True).is_relative_to(cursors.resolve()):
            raise ValueError(f'Legacy cursor escapes its directory: {p.name}')
    tmp = args.workspace_root.resolve(strict=True) / 'tmp'
    tmp.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='bibata-svg-build-', dir=tmp))
    out = work / (args.variant + '-GNOME51')
    out.mkdir()
    scalable = out / 'cursors_scalable'
    scalable.mkdir()
    shutil.copytree(cursors, out / 'cursors', symlinks=True)
    shutil.copyfile(source / 'LICENSE', out / 'LICENSE')
    (out / 'index.theme').write_text(
        '[Icon Theme]\nName=' + args.variant + ' (GNOME 51)\n'
        'Comment=Bibata SVG companion with legacy Xcursors\nInherits=Adwaita\n'
    )
    hashes: dict[str, str] = {}
    count = 0
    for key, cfg in config.items():
        name = cfg['x11_name']
        if not re.fullmatch(r'[A-Za-z0-9_-]+', name):
            raise ValueError(f'Unsafe cursor name: {name}')
        folder = scalable / name
        folder.mkdir()
        pattern = cfg['png'].replace('.png', '.svg')
        # Explicit directory glob follows Bibata's symlinked animation folders.
        frames = sorted((svg_dir / key).glob(pattern)) if '*' in pattern else [svg_dir / pattern]
        if not frames or not all(p.is_file() for p in frames):
            raise ValueError(f'Missing artwork: {key}: {pattern}')
        metadata = []
        for frame in frames:
            if not frame.resolve().is_relative_to(source):
                raise ValueError(f'Artwork escapes source tree: {frame}')
            raw = frame.read_bytes()
            hashes[str(frame.relative_to(source))] = hashlib.sha256(raw).hexdigest()
            text = raw.decode()
            for color in render['colors']:
                text = re.sub(re.escape(color['match']), color['replace'], text, flags=re.I)
            svg = ET.fromstring(text)
            if svg.get('width') != '256' or svg.get('height') != '256':
                raise ValueError(f'Recheck nominal size for non-256 artwork: {frame}')
            target = folder / frame.name
            target.write_text(text)
            result = subprocess.run(
                [renderer, '--width', '24', '--height', '24', str(target)],
                capture_output=True, check=True,
            )
            if not result.stdout.startswith(b'\x89PNG\r\n\x1a\n'):
                raise ValueError(f'Renderer did not produce PNG: {frame}')
            x = cfg.get('x_hotspot', fallback['x_hotspot'])
            y = cfg.get('y_hotspot', fallback['y_hotspot'])
            if not (0 <= x < 256 and 0 <= y < 256):
                raise ValueError(f'Hotspot outside artwork: {name}')
            delay = cfg.get('x11_delay', fallback['x11_delay']) if len(frames) > 1 else 0
            if len(frames) > 1 and delay <= 0:
                raise ValueError(f'Invalid animation delay: {name}')
            metadata.append(dict(filename=frame.name, hotspot_x=x, hotspot_y=y,
                                 nominal_size=256, delay=delay))
            count += 1
        (folder / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
        for alias in cfg.get('x11_symlinks', []):
            if not re.fullmatch(r'[A-Za-z0-9_-]+', alias):
                raise ValueError(f'Unsafe alias: {alias}')
            (scalable / alias).symlink_to(name, target_is_directory=True)
    if not (scalable / 'all-resize').exists():
        (scalable / 'all-resize').symlink_to('move', target_is_directory=True)
    for name in REQUIRED:
        metadata_path = scalable / name / 'metadata.json'
        if not metadata_path.is_file():
            raise ValueError(f'Required cursor missing: {name}')
        for frame in json.loads(metadata_path.read_text()):
            if not (metadata_path.parent / frame['filename']).is_file():
                raise ValueError(f'Metadata references missing frame: {name}')
    for p in scalable.iterdir():
        if not p.resolve(strict=True).is_relative_to(scalable):
            raise ValueError(f'Alias escapes scalable directory: {p}')
    provenance = dict(
        upstream='https://github.com/ful1e5/Bibata_Cursor', tracking_branch='main',
        ref=args.ref, commit=args.commit, variant=args.variant,
        source_sha256=hashes, svg_frames=count, required_shapes=len(REQUIRED),
        legacy_theme=str(legacy),
        conversion='Official colors, hotspots and frame delays; nominal_size=256; all-resize aliases move',
    )
    (out / 'SOURCE.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(f'Validated {count} SVG frames, {len(REQUIRED)} shapes, '
          f'{len(list(scalable.iterdir()))} names/aliases')
    print(out)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--legacy-theme', type=Path, required=True)
    parser.add_argument('--workspace-root', type=Path, required=True)
    parser.add_argument('--variant', choices=VARIANTS, default=VARIANTS[0])
    parser.add_argument('--commit', required=True)
    parser.add_argument('--ref', required=True)
    args = parser.parse_args()
    try:
        build(args)
    except (OSError, ValueError, KeyError, ET.ParseError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'Build failed; retained task files under workspace tmp: {exc}\n')


if __name__ == '__main__':
    main()
