#!/usr/bin/env python3
"""Prepare one registered package from a public GitHub release or a declared download host; never push."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\Z")
CHECKSUM = re.compile(r'[0-9a-f]{64}')


def version_tuple(value):
    if not VERSION.fullmatch(value):
        raise ValueError("Only stable X.Y.Z versions are supported")
    return tuple(map(int, value.split('.')))


def registry(root=ROOT):
    packages = json.loads((root / 'packages.json').read_text())
    paths = set()
    for name, package in packages.items():
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
            raise ValueError(f'Invalid package name: {name}')
        if not re.fullmatch(r'viaductindustries/[A-Za-z0-9_.-]+', package['repository']):
            raise ValueError('Package source must be a Viaduct Industries repository')
        if package['path'] not in (f'Casks/{name}.rb', f'Formula/{name}.rb'):
            raise ValueError('Package path must match its registered name')
        if package['path'] in paths:
            raise ValueError('Duplicate package path')
        paths.add(package['path'])
        if package['template'] != f'templates/{name}.rb.in':
            raise ValueError('Unexpected template path')
        if '/' in package['asset'] or package['asset'].count('{version}') != 1:
            raise ValueError('Asset must be a filename containing one {version}')
        template = (root / package['template']).read_text()
        if template.count('@VERSION@') < 1 or template.count('@SHA256@') != 1:
            raise ValueError('Template needs a version placeholder and one checksum placeholder')
        if 'download' in package:
            check_download(package, template)
    return packages


# Packages whose source repository is private can publish their downloads elsewhere (for example an R2 bucket).
# They declare an https folder URL containing one {version}; the folder holds the asset and SHA256SUMS.txt.
DOWNLOAD = re.compile(r'https://[A-Za-z0-9.-]+(?::[0-9]+)?/(?:[A-Za-z0-9._~-]+/)*\{version\}/(?:[A-Za-z0-9._~-]+/)*')


def check_download(package, template):
    download = package['download']
    segments = download.split('/')[3:]
    if not DOWNLOAD.fullmatch(download) or download.count('{version}') != 1 or {'.', '..'} & set(segments):
        raise ValueError('Download must be an https folder URL containing one {version} and ending in /')
    if not package['path'].startswith('Casks/'):
        raise ValueError('Hosted downloads are only supported for casks')
    # The cask must fetch exactly the folder the updater verified.
    url = (download + package['asset']).replace('{version}', '#{version}')
    if f'url "{url}"' not in template:
        raise ValueError(f'Template URL must be url "{url}"')


def hosted_asset(package, version):
    """URLs of a hosted asset and its SHA256SUMS.txt for a version."""
    folder = package['download'].format(version=version)
    return folder + package['asset'].format(version=version), folder + 'SHA256SUMS.txt'


def fetch(url, limit=None):
    request = urllib.request.Request(url, headers={'User-Agent': 'viaduct-homebrew-updater'})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read(limit) if limit else response.read()


def sha256_hosted(package, version):
    """Downloads a hosted asset and checks it against the SHA256SUMS.txt published beside it."""
    asset_url, sums_url = hosted_asset(package, version)
    name = package['asset'].format(version=version)
    published = None
    for line in fetch(sums_url, 64 * 1024).decode('utf-8').splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip('*') == name:
            published = parts[0].lower()
    if not published or not CHECKSUM.fullmatch(published):
        raise ValueError(f'SHA256SUMS.txt has no checksum for {name}')
    digest = hashlib.sha256()
    request = urllib.request.Request(asset_url, headers={'User-Agent': 'viaduct-homebrew-updater'})
    with urllib.request.urlopen(request, timeout=60) as response:
        while chunk := response.read(1024 * 1024):
            digest.update(chunk)
    checksum = digest.hexdigest()
    if checksum != published:
        raise ValueError('Downloaded checksum differs from the published SHA256SUMS.txt')
    return checksum


def release_asset(release, package, tag):
    if release['tag_name'] != tag or release['draft'] or release['prerelease']:
        raise ValueError('Expected a published stable release with the requested tag')
    name = package['asset'].format(version=tag[1:])
    assets = [a for a in release['assets'] if a['name'] == name]
    if len(assets) != 1 or assets[0].get('state') != 'uploaded' or assets[0]['size'] <= 0:
        raise ValueError(f'Release asset is missing or incomplete: {name}')
    url = assets[0]['browser_download_url']
    expected = f"https://github.com/{package['repository']}/releases/download/{tag}/{name}"
    if urllib.parse.unquote(url) != expected:
        raise ValueError('Unexpected asset download URL')
    return assets[0]


def sha256_download(asset):
    digest = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(asset['browser_download_url'], timeout=60) as response:
        while chunk := response.read(1024 * 1024):
            size += len(chunk)
            digest.update(chunk)
    if size != asset['size']:
        raise ValueError('Downloaded size differs from release asset metadata')
    checksum = digest.hexdigest()
    if asset.get('digest') and asset['digest'] != f'sha256:{checksum}':
        raise ValueError('Downloaded checksum differs from GitHub asset digest')
    return checksum


def parse(current, template):
    """Return the version and checksum of a definition rendered from template."""
    pattern, seen_version = '', False
    for part in re.split('(@VERSION@|@SHA256@)', template):
        if part == '@SHA256@':
            pattern += '(?P<sha256>[0-9a-f]{64})'
        elif part == '@VERSION@':
            # Repeated placeholders must all hold the same version.
            pattern += '(?P=version)' if seen_version else '(?P<version>[0-9.]+)'
            seen_version = True
        else:
            pattern += re.escape(part)
    match = re.fullmatch(pattern, current)
    if not match:
        raise ValueError('Definition differs from its reviewed template; update both together')
    version_tuple(match['version'])
    return match['version'], match['sha256']


def render(current, template, version, checksum):
    version_tuple(version)
    if not CHECKSUM.fullmatch(checksum):
        raise ValueError('Expected a SHA-256 checksum')
    if current is not None:
        old, old_checksum = parse(current, template)
        if version_tuple(version) < version_tuple(old):
            raise ValueError(f'Refusing downgrade from {old} to {version}')
        if version == old and checksum != old_checksum:
            raise ValueError('Refusing to replace the checksum for an existing version')
    return template.replace('@VERSION@', version).replace('@SHA256@', checksum)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', required=True)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--source-repository', required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    packages = registry()
    if args.package not in packages:
        raise ValueError('Unknown package; register it in a reviewed PR first')
    package = packages[args.package]
    if args.source_repository != package['repository']:
        raise ValueError('Calling repository does not own this package')
    if not args.tag.startswith('v'):
        raise ValueError('Release tags must start with v')
    version = args.tag[1:]
    version_tuple(version)
    if 'download' in package:
        # The source repository may be private, so its release can't be read here; the caller's identity
        # (checked above) and the published checksum file vouch for the hosted asset instead.
        checksum = sha256_hosted(package, version)
    else:
        request = urllib.request.Request(
            f"https://api.github.com/repos/{package['repository']}/releases/tags/{args.tag}",
            headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'viaduct-homebrew-updater'})
        with urllib.request.urlopen(request, timeout=30) as response:
            release = json.load(response)
        asset = release_asset(release, package, args.tag)
        checksum = sha256_download(asset)
    path = ROOT / package['path']
    current = path.read_text() if path.exists() else None
    result = render(current, (ROOT / package['template']).read_text(), version, checksum)
    changed = result != current
    if args.dry_run:
        print(result, end='')
    elif changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(result)
    if output := os.environ.get('GITHUB_OUTPUT'):
        with open(output, 'a') as stream:
            stream.write(f'changed={str(changed).lower()}\npath={package["path"]}\nversion={version}\n')
    print(f'{args.package}: {args.tag}, sha256={checksum}, changed={changed}')


if __name__ == '__main__':
    main()
