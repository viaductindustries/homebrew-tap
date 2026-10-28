#!/usr/bin/env python3
"""Validate registry/templates and forbid package downgrades against a base commit."""
import argparse
import subprocess
from update_package import ROOT, registry, VERSION_LINE, HASH_LINE, version_tuple


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
        current = path.read_text()
        versions, hashes = VERSION_LINE.findall(current), HASH_LINE.findall(current)
        if len(versions) != 1 or len(hashes) != 1:
            raise ValueError(f'{name}: expected one stable version and SHA-256')
        version_tuple(versions[0])
        expected = template.read_text().replace('@VERSION@', versions[0]).replace('@SHA256@', hashes[0])
        if current != expected:
            raise ValueError(f'{name}: definition differs from reviewed template; update both together')
        subprocess.run(['ruby', '-c', str(path)], check=True)
        if args.base:
            old = subprocess.run(['git', 'show', f'{args.base}:{package["path"]}'],
                                 capture_output=True, text=True)
            if old.returncode == 0:
                old_versions, old_hashes = VERSION_LINE.findall(old.stdout), HASH_LINE.findall(old.stdout)
                if len(old_versions) != 1 or len(old_hashes) != 1:
                    raise ValueError(f'{name}: invalid base definition')
                if version_tuple(versions[0]) < version_tuple(old_versions[0]):
                    raise ValueError(f'{name}: version downgrade')
                if versions == old_versions and hashes != old_hashes:
                    raise ValueError(f'{name}: checksum changed without a version bump')
    registered = {p['path'] for p in registry().values()}
    actual = {str(p.relative_to(ROOT)) for directory in ['Casks', 'Formula']
              for p in (ROOT / directory).glob('*.rb')}
    if actual - registered:
        raise ValueError(f'Unregistered definitions: {actual - registered}')


if __name__ == '__main__':
    main()
