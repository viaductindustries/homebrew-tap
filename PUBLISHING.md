# Publishing to the Viaduct Industries tap

This guide is for Viaduct Industries developers distributing a project through this tap, and for maintainers of the tap itself. For installation instructions, see the [README](README.md).

macOS applications are distributed as casks in `Casks/`; command-line tools are formulae in `Formula/`. Each project builds, signs and hosts its own releases on GitHub. This tap only holds the installation definitions and verified checksums, and keeps them current through reviewed pull requests opened automatically when a project publishes a release. No placeholder checksums or `sha256 :no_check` are used.

## How it works

1. A source project finishes publishing an immutable GitHub release containing its download.
2. Its release workflow calls this tap's reusable `update-package.yml` with the package name and `vX.Y.Z` tag. GitHub supplies the caller's repository identity; callers cannot override it.
3. The updater checks that repository owns the package in `packages.json`, rejects drafts and prereleases, finds the exact expected asset, downloads it and computes its SHA-256. It also checks the size and GitHub's asset digest when available.
4. It changes only the version and checksum in an existing definition, or creates the first definition from the package's reviewed template.
5. It opens an `automation/<package>/<version>` PR. Each package has its own branches, so projects publish independently. Repeated calls reuse an existing open PR; already-merged identical definitions are a no-op. Closed update PRs require a maintainer to reopen them or publish a newer version.
6. PR checks run with read-only credentials on disposable runners. Casks are installed into a temporary application directory, and registered `.app` bundles must pass code-signature, stapling and Gatekeeper checks. Formulae are built from source and run their `test` block.
7. A maintainer merges the PR. Users receive it with `brew update` and install it with `brew upgrade`.

Updates for a package are serialized within its owning repository. An older version racing a newer PR cannot replace the newer version on `main`: the updater and validation reject downgrades, and the required up-to-date branch rule reruns those checks before merge. Close superseded open PRs during review.

## Supported releases

The updater currently supports:

- public GitHub repositories in the `viaductindustries` organization;
- stable `vX.Y.Z` tags;
- one versioned asset and checksum per package.

Universal macOS ZIPs fit this model. Separate Intel/ARM downloads, prerelease channels, non-GitHub downloads and bottle publishing require extending the registry and updater first. CI runs on the Apple Silicon `macos-26` runner; add Intel or Linux jobs when registering packages that target those systems.

Signing and notarization stay in the source project. This tap never needs Apple credentials.

## Adding a package

1. **Template.** Add `templates/<name>.rb.in`, where `<name>` is the lowercase, hyphenated Homebrew token. It needs exactly one `  sha256 "@SHA256@"` line and a URL to the project's GitHub release asset. The updater fills in every `@VERSION@` and checks that existing definitions still match the template.

   Casks declare `  version "@VERSION@"` and interpolate it in the URL:

   ```ruby
   url "https://github.com/viaductindustries/<repo>/releases/download/v#{version}/<Asset>-#{version}.zip"
   ```

   Formulae must not declare an explicit `version` (Homebrew's style and audit checks reject it), so the URL carries the placeholder directly:

   ```ruby
   url "https://github.com/viaductindustries/<repo>/releases/download/v@VERSION@/<asset>_@VERSION@_source.tar.gz"
   ```

   Casks should declare `name`, `desc`, `homepage`, any `depends_on` and the installed artifacts. Formulae need a valid build/install definition and a meaningful `test` block. Bottle publishing is not configured, so formulae build from a source archive uploaded to the release (GitHub's automatic source archives are not release assets).

2. **Registry.** Add an entry to `packages.json`:

   ```json
   "<name>": {
     "repository": "viaductindustries/<repo>",
     "path": "Casks/<name>.rb",
     "template": "templates/<name>.rb.in",
     "asset": "<Asset>-{version}.zip",
     "app": "<App Name>.app"
   }
   ```

   Use `Formula/<name>.rb` for command-line tools. Include `app` for app casks so CI verifies the bundle's signature and notarization; omit it for formulae. Casks for PKG installers or other non-app artifacts need additional CI verification before registration.

3. **Review.** Review the installation instructions, dependencies and caveats. Add the package to the README's Packages table, with any requirements users need to know about.

4. **Source project.** Ask a tap maintainer to grant the source repository access to the publisher credentials, then add a caller job after its release upload, adapted from [`examples/cert-lab-publish.yml`](examples/cert-lab-publish.yml): set `package`, keep `needs:` pointing at the job that uploads the finished asset, and pin the tap workflow to a full reviewed commit SHA. If the source workflow is itself reusable with explicitly named secrets, declare and pass `HOMEBREW_APP_PRIVATE_KEY` through it too; the client ID is an Actions variable.

5. **First release.** Publish a release, review the generated PR, confirm installation checks pass, and merge it. The package is installable from then on.

## When an update fails

Nothing is rebuilt here, and an existing version's checksum cannot change without a version bump. A tap update failure does not invalidate the upstream release; after resolving missing assets or credentials, retry only the caller's Homebrew job.

If a push succeeded but PR creation failed, the workflow verifies the existing branch tree before reusing it. If `main` has since advanced and the branch no longer matches, review that branch manually instead of force-pushing it.

## Local checks

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate.py
```

To preview a definition without writing files or opening PRs, once a release asset exists:

```sh
python3 scripts/update_package.py \
  --package <name> --tag vX.Y.Z \
  --source-repository viaductindustries/<repo> --dry-run
```

Without `--dry-run`, that command writes only the local definition; it does not commit or push. `scripts/check_installations.py` installs and removes packages and is intended for disposable CI runners, not a maintainer's normal environment.

## Repository layout

- `packages.json`: registry of packages, their owning repositories, definition paths, templates and release asset names.
- `templates/<name>.rb.in`: reviewed initial definitions. The updater fills in the verified version and checksum.
- `Casks/<name>.rb`: installable macOS applications, added only once a verified release exists.
- `Formula/<name>.rb`: installable command-line tools, added only once a verified release exists.
- `scripts/update_package.py`: verifies a public stable release, downloads its asset, and prepares one definition.
- `scripts/validate.py`: checks the registry, templates and definitions, and rejects downgrades or changed checksums.
- `scripts/check_installations.py`: installs and verifies every published package. CI only.
- `.github/workflows/update-package.yml`: reusable workflow that prepares an update and opens a PR using a GitHub App token.
- `.github/workflows/validate.yml`: updater tests, registry validation, Homebrew style/audit and installation checks.
- `examples/cert-lab-publish.yml`: example caller job for a source project's release workflow.

## Security model

The GitHub App token is minted only after the release asset has been verified, is scoped to this tap, and is revoked when the job completes. Do not grant publisher credentials to untrusted repositories: GitHub cannot restrict an App to individual files, so the package registry prevents accidental cross-project updates but is not a security boundary against a repository holding the App's private key.

The reusable workflow loads the current reviewed tap `main` for its registry, templates and scripts. Pinning the caller pins the workflow entry point, not that centrally maintained catalogue. Treat changes to scripts, templates and workflows here as trusted publishing changes.

## Maintaining the tap

### First-time GitHub setup

This is done once for the tap, not per package.

1. Review and commit this scaffold, create the public `viaductindustries/homebrew-tap` repository, and push `main`. The scaffold intentionally does not perform these remote operations.
2. Create an organization-owned GitHub App, for example **Viaduct Homebrew Publisher**. Give it repository **Contents: read/write** and **Pull requests: read/write**. Webhooks and user authorization are unnecessary. Install it on **only `homebrew-tap`**.
3. Record its **Client ID** as the Actions variable `HOMEBREW_APP_CLIENT_ID`. Generate a private key and store the complete PEM text (not base64) as the Actions secret `HOMEBREW_APP_PRIVATE_KEY`. Define both at the organization level, restricted to the approved source repositories, so each new package only needs its repository added to that list. Store a backup of the key in 1Password.
4. Protect `main`: require PRs, require the **Validate definitions and updater** check, and require branches to be up to date before merging. The last rule ensures an older outstanding update cannot downgrade a version merged by another PR. Start with maintainer review required and automatic merging disabled.
5. Onboard each package using [Adding a package](#adding-a-package).

### Reviewing update PRs

Check that the PR changes only the version and checksum of one package, that validation passed, and that the version is newer than any other open update for that package. Close superseded PRs.

### Later automation

After a few successful releases, consider automatic merging only for publisher-created PRs that change version/checksum lines in existing definitions, pass all checks, and are up to date. New packages and changes to installation rules, templates, the registry or workflows should keep human review. Automatic merging is not enabled.

## References

- [Homebrew taps](https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap)
- [Cask cookbook](https://docs.brew.sh/Cask-Cookbook)
- [Formula cookbook](https://docs.brew.sh/Formula-Cookbook)
- [GitHub App authentication](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/making-authenticated-api-requests-with-a-github-app-in-a-github-actions-workflow)
