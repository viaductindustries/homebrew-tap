# Agent guidance

This repository is the shared Viaduct Industries Homebrew tap.

- Use Conventional Commits. Do not push, create remote repositories, change GitHub settings, or merge PRs unless asked.
- Never put credentials in the repository. Source projects own Apple signing/notarization; this tap only distributes their finished assets.
- Register each package's owning repository in `packages.json`. Keep templates and installed definitions consistent.
- Do not invent release checksums, use `sha256 :no_check`, downgrade package versions, or change the hash for an existing version.
- Keep the publisher restricted to one package per PR. Initial definitions require reviewed templates; automatic updates change version/checksum only.
- Run `python3 -m unittest discover -s tests -v`, `python3 scripts/validate.py`, and actionlint before committing workflow/updater changes.
- Installation checks belong on disposable CI runners. Do not install/uninstall packages on the maintainer's machine without explicit authorization.
- Keep manual review for initial packages, installation changes and publisher infrastructure. Automatic merging is not yet enabled.
