# Upstream maintenance

The daily workflow tracks version properties in `chililisoup/neoforge-carpet`. `master` is informational; only `1.20.1` can produce a port. Updates without a version-property change wait for the next version. No source code from the upstream checkout is executed.

## Installation and first baseline

The scheduled workflow must exist on the GitHub repository's default branch (GitHub scheduling requirement); its checkout explicitly targets `1.20.1-tick`. Install both `upstream-sync.yml` and the matching reusable `publish-release.yml` on the default branch when deploying these changes: relative reusable workflow calls resolve from the caller's commit. Scripts and runtime code are checked out from `1.20.1-tick`. Enable Actions and allow `contents: write` and the bot's normal fast-forward under branch protection. No token or protection bypass is configured. Manual dispatch is also supported. This local checkout does not activate hosted automation by itself.

Run `python .github/scripts/upstream.py scan` to discover versions. The initial 1.20.1 snapshot needs a manual comparison against this reduced port: confirm the retained commands, tick controller, profiler behavior and mixin integration, documenting intentional differences. Pass build and GameTests, then run `python .github/scripts/upstream.py approve-baseline --sha <full detected SHA>`. Commit the resulting state and document blocks. Approval asserts correspondence; the script cannot establish it for you.

Missing baseline or unknown changes show review-required status, never an applied/verified version. `master` has no applied status. A version-only update advances the reviewed snapshot but leaves the last code-applied snapshot intact.

## Reviewed conversion rules

The rule registry starts empty: future source edits must not be guessed. After reviewing a particular change, add a rule to `.github/upstream-rules.json`. Keys are `from_sha`, `to_sha`, `from_fingerprint`, `to_fingerprint`, `base_local_sha256`, `bump` (`patch`, `minor`, or `major`), `summary`, and `edits`.

Each edit contains `path` (existing runtime file under `src/tick`, excluding the development GameTest), `before_sha256`, full replacement `content`, and `after_sha256`. Hashes use UTF-8 text with normalized LF newlines. Use `local_fingerprint` and `digest` in `.github/scripts/upstream.py` to calculate local fingerprints; upstream commit/fingerprint values are stored in state. A rule covers the entire upstream snapshot delta, including indirect source, resource, and build changes. Do not approve a rule based only on TickCommand.java or successful compilation.

Exact fingerprints prevent applying a rule to a different version or locally modified implementation. Rules cannot write workflows, version files, arbitrary paths, or invoke shell commands. The updater handles changelog and SemVer separately. Rules may include explicitly reviewed compatibility adaptations; new/unrecognized changes wait for another reviewed rule. Rules are retried for an already detected version after review, without waiting for another version bump.

## Validation and publication

Candidates run updater tests and the common-JAR compatibility matrix before the target branch is advanced. Forge 47.4.0/47.4.20 and NeoForge 47.1.5/47.1.106 must pass build, GameTests, packaging/content equality and conflict rejection. Failed code candidates are discarded; the failure is retained in state and documentation. Fetch failures keep the last detected versions. Identical failures are deduplicated. A branch race or push permission failure is visible in the failed workflow and uploaded evidence, since the bot may be unable to commit that failure.

The reusable release workflow explicitly publishes the verified commit after a successful automated update. It builds again, checks packaged metadata/classes, keeps tags immutable and retries an unpublished automatic version on later runs. An existing tag is reused for publication retries. Documentation-only changes do not initiate a new release. Manual release versions must match committed properties.

All Markdown status blocks come from `.github/upstream-state.json`. Run `python .github/scripts/upstream.py render` after manual state edits; `check` rejects stale/malformed blocks. Historical changelog entries and dated audit results remain unchanged. Full failure details are in the state file; `upstream-update-evidence` and `release-verification` artifacts contain logs/reports for command-level regression results. GitHub Issue notifications are not enabled.

## Conflict behavior

Verified original/full ports share the ID `carpet`. A mixin plugin checks the discovered mod list before our mixins run, and a constructor check provides a fallback. A conflict fails startup with the original mod's name, ID and version and tells the user to use the original Carpet mod and remove this one. No mod files are deleted. Unknown fork IDs and Fabric JARs ignored/rejected by Forge are not claimed as detected.

## Local checks

```text
python -m unittest discover -s .github/scripts -p "test_*.py" -v
python .github/scripts/upstream.py check
python .github/scripts/verify-compatibility.py
```

Do not change `run/eula.txt`. GameTests use the vanilla template namespace and require no normal-server EULA edit.

<!-- upstream-status:start -->
## Upstream tracking status

Source: [chililisoup/neoforge-carpet](https://github.com/chililisoup/neoforge-carpet). Detected versions are not a compatibility claim.

| Branch | Latest detected | Reviewed | Applied and verified | Status |
| --- | --- | --- | --- | --- |
| master | 1.4.147-port-1.0.8 (`44360a01d00b`) | Not verified | Not verified | informational-only |
| 1.20.1 | 1.4.112-port-1.0.8 (`4b3f3ddc7312`) | Not verified | Not verified | baseline-review-required |

Failure history: 2 distinct event(s). Details: `.github/upstream-state.json`; command test results: GitHub Actions artifacts.
<!-- upstream-status:end -->
