# TICEagle/publish

This action publishes a release of your TI-84 Plus CE project on [CEagle](https://ceagle.cc) from GitHub Actions, without storing any secret. It downloads the `ceagle` command-line tool, checks its sha256 against the one pinned in this repository, and runs `ceagle publish` next to your `ceagle.toml`. CEagle trusts the run through GitHub's OIDC token, the same way PyPI's trusted publishing works.

## Set up trusted publishing

1. Write a `ceagle.toml` for your project. The [`ceagle` README](https://github.com/TICEagle/cli) explains the keys.
2. On ceagle.cc, open your project's Publishing page and add a trusted publisher: your GitHub repository, the workflow file name (`release.yml` in the example below) and, if you use one, the GitHub environment (`release`).
3. Give the job `permissions: id-token: write`. Without it GitHub hands out no OIDC token and the publish stops with `publishing needs a token`.
4. Give it `attestations: write` too, so the release carries a build provenance attestation (below).

CEagle stores the numeric ids of your repository and its owner, so a deleted and recreated repository with the same name can't publish. Each GitHub token works once, and the CEagle token it is exchanged for only publishes to that one project for 15 minutes.

## Example
```yaml
name: release

on:
  push:
    tags: ['v*']

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: release
    permissions:
      id-token: write
      attestations: write
      contents: read
    steps:
      - uses: actions/checkout@v7
        with:
          persist-credentials: false
      - run: |
          curl -fsSL https://github.com/CE-Programming/toolchain/releases/download/v15.0/CEdev-Linux.tar.gz | tar xz -C "$RUNNER_TEMP"
          echo "$RUNNER_TEMP/CEdev/bin" >> "$GITHUB_PATH"
      - run: make
      - uses: TICEagle/publish@v1
        with:
          version: ${{ github.ref_name }}
          notes: CHANGELOG.md
```

A tag like `v1.2` is fine as the version: `ceagle` turns it into `1.2.0`.

## Inputs

| Input | Default | Meaning |
| --- | --- | --- |
| `version` | required | Version to publish, like `1.2.0` or `${{ github.ref_name }}` |
| `notes` | none | Path to a release notes file, at most 32 KiB, relative to `working-directory` |
| `working-directory` | `.` | Folder that holds `ceagle.toml` |
| `api-url` | `https://ceagle.cc` | CEagle server |
| `cli-version` | `1.1.0` | Version of `ceagle` to run. Each version of this action pins the sha256 of the versions it knows in `checksums/`, and refuses any other |
| `token` | none | A CEagle API token, for when you can't use trusted publishing. Pass it from a secret. When it is empty, the action uses trusted publishing |
| `attest` | `true` | Attest the release files with Sigstore and send the attestation with the release. Only with trusted publishing from a public repository |

## Outputs

| Output | Meaning |
| --- | --- |
| `status` | `published`, `under_review`, `rejected` or `processing` |
| `url` | Page of the release on CEagle, like `https://ceagle.cc/p/mazerun/1.2.0`. Only set when it was published |

## When the step fails

| Result | `status` | Step |
| --- | --- | --- |
| Published | `published` | Succeeds |
| Under review: a CEagle admin looks at it first and you get an email | `under_review` | Succeeds with a warning |
| Still processing after 10 minutes: CEagle keeps working on it | `processing` | Succeeds with a warning |
| Rejected, the reason is in the log | `rejected` | Fails |
| Problems to fix in `ceagle.toml`, the files or the version | none | Fails, `ceagle` lists every problem |
| No token, a refused token or a network error | none | Fails with `ceagle`'s message |

| No attestation: the job lacks `attestations: write`, or `ceagle` is older than the action | `published` (or another status) | Succeeds with a warning, the release has no attestation |
| The attestation does not match the release | none | Fails, `ceagle` names the problem, like `the attestation does not cover GDASH.8xp` |

To fail the job on anything but `published`, give the action an `id` and add a step with `if: steps.<id>.outputs.status != 'published'` that runs `exit 1`.

## Build provenance

With trusted publishing from a public repository, the action runs `ceagle checksums` to list the release files with their sha256, attests exactly those files with [`actions/attest-build-provenance`](https://github.com/actions/attest-build-provenance) (pinned by commit), and passes the Sigstore bundle to `ceagle publish --attestation`. CEagle checks the bundle against the Sigstore public good instance and refuses the release unless it was made by your trusted publisher's repository and workflow, at the commit and in the run that publishes, and covers every file and nothing else. The release page then shows the build as verified and links the bundle.

Anyone can check a downloaded file against your repository, with the attestation GitHub keeps or with the one from CEagle:

```sh
gh attestation verify MAZERUN.8xp --repo you/mazerun
gh attestation verify MAZERUN.8xp --repo you/mazerun --bundle mazerun-1.2.0.sigstore.json
```

The attestation is skipped with `token`, in private repositories (GitHub signs those with its own Sigstore instance, which CEagle does not trust) and with `attest: false`. If the attestation can't be made, for example without `attestations: write`, the release is published without one and the step shows a warning.

## Runners

The action runs on GitHub-hosted Linux (x64 and arm64), macOS (Intel and Apple silicon) and Windows (x64) runners. It needs `bash` and the GitHub CLI `gh`, which every GitHub-hosted runner has. After the step, `ceagle` stays on the `PATH` for the rest of the job.

## License

This action is free software under the GNU General Public License, version 3. See `LICENSE`.
