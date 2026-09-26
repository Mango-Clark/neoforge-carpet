# Project instructions

This branch (`1.20.1-tick`) is a lightweight Minecraft 1.20.1 Forge 47.4.x port of Carpet's `/tick` command, targeting Forge 47.4.20. Preserve the tick-only scope: the mod registers `/tick` only; do not restore Carpet rules, Scarpet, other Carpet commands, or client-side features without an explicit request. Mod ID is `neoforge_carpet_tick` and the display/project name is `neoforge-carpet-tick`.

## Versioning

- `gradle.properties` is the version source. Keep `carpet_version=1.4.112` fixed: it is the upstream Carpet base version, not the release counter for this port.
- Change only `tick_version` for subsequent releases. Use SemVer `MAJOR.MINOR.PATCH` without leading zeroes; increment it according to compatibility (patch for compatible fixes, minor for compatible features, major for incompatible changes).
- Gradle derives mod version `<carpet_version>-tick-<tick_version>` and artifact name `neoforge-carpet-<carpet_version>-tick-<tick_version>.jar`. Current values yield `1.4.112-tick-1.0.0` and `neoforge-carpet-1.4.112-tick-1.0.0.jar`. Keep generated `mods.toml` version and JAR version aligned; do not put the Minecraft version in the artifact name.
- A push to `1.20.1-tick` publishes a GitHub Release only when `tick_version` changes relative to the previous push commit. Do not bump it for ordinary build or documentation changes. Use a new version for every release; existing tags must not be moved. Update `CHANGELOG.md` with notable changes before bumping the version.

## Layout and checks

- Runtime code and mixins: `src/tick/java/dev/clark/carpet_tick`; resources: `src/tick/resources`; mod metadata template: `src/tick/templates/META-INF/mods.toml`.
- `TickGameTests.java` is a development GameTest source and is excluded from the distributable JAR. Keep the `minecraft` GameTest namespace because its template uses a vanilla Minecraft structure.
- Run `./gradlew build runGameTestServer` (Windows: `.\gradlew.bat build runGameTestServer`) after changes; `build` alone does not execute GameTests. Java 17 is the compilation/game target. This checkout has used Java 21 for Gradle.
- Check `build/libs` for the expected artifact name and confirm the packaged JAR excludes `TickGameTests.class` and legacy `carpet/` classes.
- A normal server launch needs its own EULA acceptance. Do not change `run/eula.txt` on the user's behalf; `runGameTestServer` can validate without it.
- `docs/lightweight-audit.md` records the prior footprint and verification limits. Update version-specific artifact references there when changing packaging.

## Upstream automation decisions

- Track only `chililisoup/neoforge-carpet`: `master` for information, `1.20.1` for automatic ports. Poll daily at 03:17 UTC and support manual workflow dispatch. Process only changes to upstream `carpet_version` or `port_version`; same-version commits wait until the next version change. Do not follow Fabric Carpet separately.
- Keep Minecraft 1.20.1, Forge 47.4.20/47.4.x, the tick-only scope, mod identity, fixed upstream base `carpet_version=1.4.112`, and artifact naming unchanged. Latest detected upstream versions are separate tracking data, never a replacement for the fixed base.
- `.github/upstream-state.json` is the tracking source of truth: detected, reviewed, and applied/verified snapshots are distinct. The initial snapshot is NOT automatically verified. After manually comparing the port and passing tests, approve its exact SHA with `python .github/scripts/upstream.py approve-baseline --sha <SHA>`.
- Assess the full upstream source/resource/build dependency closure conservatively, not only filenames containing tick. Documentation/CI-only changes and the two version properties are excluded; unknown source changes require review.
- Automatic code changes require an explicitly reviewed rule in `.github/upstream-rules.json`: exact old/new commits and source fingerprints, exact local implementation fingerprint, runtime file before/after hashes, replacement content, SemVer classification, and changelog summary. No AI service, upstream build execution, arbitrary patch commands, or guessed transformations. An empty rule registry intentionally blocks unknown ports.
- Uncertain changes, unsupported APIs, missing baseline, source fetch failure, stale rule, failed build/GameTests, or target-branch races block code publication. Preserve last known versions and distinct failure history. Never label an unavailable source as unchanged or verified. Repeated identical failures must not create new commits.
- Work on an isolated candidate branch. Validate before fast-forwarding `1.20.1-tick`; recheck its original SHA before pushing. Failed runtime changes are discarded while status/failure documentation is retained. Branch protection is respected, never bypassed.
- No runtime change means documentation/state updates only: no `tick_version` bump, new tag, or release replacement. Self-authored features and fixes may also be released. Compatible fixes use patch, compatible features minor, incompatible changes major; ambiguous classification requires review. Write CHANGELOG before bumping.
- Explicitly call the reusable release workflow after a verified automatic update; do not rely on GITHUB_TOKEN pushes triggering workflows. Publish the tested commit, keep existing tags immutable, and retry a failed publication using its existing tag when present. Manual release input must match checked-in properties; it cannot override the JAR version.
- GitHub scheduled workflows require the workflow on the repository default branch. Deployment requires contents write permission and branch rules permitting the bot's normal fast-forward; local implementation does not imply hosted automation is enabled.
- Deploy both `upstream-sync.yml` and its matching reusable `publish-release.yml` to the default branch; relative reusable calls use the caller commit. Publication retries without a tag resolve the original version-bump commit from Git history, not later documentation commits.

## Conflict policy

- Original Carpet and verified full Carpet ports cannot run alongside this mod. The verified shared mod ID is `carpet` (Fabric original and chililisoup NeoForge/Forge ports). Add other IDs only after checking their actual metadata; do not infer IDs from filenames or block unrelated extensions.
- Detect conflicts before applying our mixins, with a constructor check as fallback. Stop startup and show the conflicting name, ID, and version. Explicitly say to use the original Carpet mod and remove neoforge-carpet-tick before restarting, in English and Korean. Never delete user mods or change their configuration automatically.
- Fabric mods not recognized by the active Forge loader are outside the detection contract; loader-level incompatibility may occur before our guard. Do not claim arbitrary JAR or every third-party fork detection.

## Documentation, evidence, and collaboration

- Every repository Markdown document has a generated upstream status block from the tracking state. Run `python .github/scripts/upstream.py render` after changes and `python .github/scripts/upstream.py check` in CI. Preserve historical release entries and dated footprint measurements outside those blocks.
- Latest detected does not mean applied or compatible. Include status table, deduplicated failure history, and command regression evidence. Keep detailed failure records in state and upload test/log artifacts; do not automatically create GitHub Issues.
- Test updater scenarios with `python -m unittest discover -s .github/scripts -p 'test_*.py' -v`; run build plus GameTests and `python .github/scripts/verify-jar.py` for runtime changes. Cover rate, freeze/deep freeze, step budget, warp, SuperHot activity, health/entities, profiler cleanup, conflict rejection, version gating, stale/unknown rules, docs consistency, and failure retries.
- Require `python .github/scripts/verify-gametests.py` immediately after GameTests: Forge loading failures can return zero. Run `python .github/scripts/test-conflict-startup.py` afterward to verify real mod discovery rejects a temporary `carpet` fixture before server start; it removes only its own fixture and preserves separate normal-test evidence. Use a fatal Mixin initialization error because ordinary plugin exceptions may be swallowed.
- Record future agreed decisions in this file. Proactively suggest relevant support improvements with benefits/costs and ask for meaningful user preferences before expanding scope. Do not repeatedly ask about already settled decisions.
- The user authorizes ordinary non-force remote operations needed for this project's work without repeated confirmation, including pushing project commits to `https://github.com/Mango-Clark/neoforge-carpet.git` on `1.20.1-tick`. Ask before force operations; never infer authorization to overwrite remote history. Respect tool approval enforcement and report any remaining rejection.

<!-- upstream-status:start -->
## Upstream tracking status

Source: [chililisoup/neoforge-carpet](https://github.com/chililisoup/neoforge-carpet). Detected versions are not a compatibility claim.

| Branch | Latest detected | Reviewed | Applied and verified | Status |
| --- | --- | --- | --- | --- |
| master | 1.4.147-port-1.0.8 (`44360a01d00b`) | Not verified | Not verified | informational-only |
| 1.20.1 | 1.4.112-port-1.0.8 (`4b3f3ddc7312`) | Not verified | Not verified | baseline-review-required |

Failure history: 2 distinct event(s). Details: `.github/upstream-state.json`; command test results: GitHub Actions artifacts.
<!-- upstream-status:end -->
