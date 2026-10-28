#!/usr/bin/env python3
"""Validate registry/templates and forbid package downgrades against a base commit."""
import argparse
import subprocess
from update_package import ROOT, registry, parse, version_tuple


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base')
    args = parser.parse_args()
    for name, package in registry().items():
        template = ROOT / package['template']
        subprocess.run(['ruby', '-c', str(template)], check=True)
        path = ROOT / package['path']
        if not path.exists():
            print(f'{name}: registered, awaiting first verified release asset')
            continue
        version, checksum = parse(path.read_text(), template.read_text())
        subprocess.run(['ruby', '-c', str(path)], check=True)
        if args.base:
            old = subprocess.run(['git', 'show', f'{args.base}:{package["path"]}'],
                                 capture_output=True, text=True)
            if old.returncode == 0:
                old_template = subprocess.run(['git', 'show', f'{args.base}:{package["template"]}'],
                                              capture_output=True, text=True, check=True)
                old_version, old_checksum = parse(old.stdout, old_template.stdout)
                if version_tuple(version) < version_tuple(old_version):
                    raise ValueError(f'{name}: version downgrade')
                if version == old_version and checksum != old_checksum:
                    raise ValueError(f'{name}: checksum changed without a version bump')
    registered = {p['path'] for p in registry().values()}
    actual = {str(p.relative_to(ROOT)) for directory in ['Casks', 'Formula']
              for p in (ROOT / directory).glob('*.rb')}
    if actual - registered:
        raise ValueError(f'Unregistered definitions: {actual - registered}')


if __name__ == '__main__':
    main()
