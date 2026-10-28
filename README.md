# Viaduct Industries Homebrew tap

Install Viaduct Industries apps and command-line tools with [Homebrew](https://brew.sh).

## Installing

```sh
brew tap viaductindustries/tap

brew install --cask <app>   # macOS applications
brew install <tool>         # command-line tools
```

You can also install without tapping first, for example:

```sh
brew install --cask viaductindustries/tap/cert-lab
```

## Updating

```sh
brew update
brew upgrade                # or: brew upgrade --cask <app>
```

New versions appear here shortly after each project publishes a release, once the update has passed checks and been reviewed.

## Uninstalling

```sh
brew uninstall --cask <app>
brew uninstall <tool>
brew untap viaductindustries/tap   # optional, once nothing from the tap is installed
```

## Packages

| Package    | Type | Description                                         | Source                                                                      |
| ---------- | ---- | --------------------------------------------------- | --------------------------------------------------------------------------- |
| `cert-lab` | Cask | Private certificate authorities backed by 1Password | [viaductindustries/cert-lab](https://github.com/viaductindustries/cert-lab) |

### Requirements

- **Cert Lab** requires macOS Sonoma (14) or later, plus the 1Password desktop app and CLI, with **Settings > Developer > Integrate with 1Password CLI** enabled. Installing the cask does not configure a 1Password account.

## Trust and verification

Every download comes directly from the project's own GitHub release. This tap pins each version to a SHA-256 checksum computed from that release, so Homebrew refuses a download that doesn't match. macOS apps are signed and notarized by their projects, and each update is checked for a valid signature, notarization and Gatekeeper approval before it is merged.

## Reporting problems

- Bugs or feature requests for an app or tool belong in that project's repository, linked in the [Packages](#packages) table.
- Problems installing, upgrading or uninstalling a package belong in this repository's issues.

## Publishing to this tap

Viaduct Industries developers adding a project or maintaining the tap should read [PUBLISHING.md](PUBLISHING.md).
