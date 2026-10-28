#!/usr/bin/env python3
"""Run only on disposable CI runners: install and validate registered packages."""
import os
from pathlib import Path
import subprocess
from update_package import ROOT, registry


def run(*args):
    subprocess.run(args, check=True)


run('brew', 'tap', 'viaductindustries/tap', str(ROOT))
for name, package in registry().items():
    if not (ROOT / package['path']).exists():
        continue
    token = f'viaductindustries/tap/{name}'
    if package['path'].startswith('Casks/'):
        appdir = Path(os.environ['RUNNER_TEMP']) / 'tap-apps'
        appdir.mkdir(exist_ok=True)
        run('brew', 'style', '--cask', token)
        run('brew', 'audit', '--cask', '--online', token)
        run('brew', 'install', '--cask', '--appdir', str(appdir), token)
        if app := package.get('app'):
            bundle = str(appdir / app)
            run('codesign', '--verify', '--deep', '--strict', bundle)
            run('xcrun', 'stapler', 'validate', bundle)
            run('spctl', '--assess', '--type', 'execute', '--verbose=2', bundle)
        run('brew', 'uninstall', '--cask', '--appdir', str(appdir), token)
    else:
        run('brew', 'style', '--formula', token)
        run('brew', 'audit', '--formula', '--online', token)
        run('brew', 'install', '--build-from-source', token)
        run('brew', 'test', token)
        run('brew', 'uninstall', token)
