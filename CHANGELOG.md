# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/).
The tick-port release counter uses Semantic Versioning in the `tick_version` field.

## [Unreleased]

### Added

- Refuse startup alongside original/full Carpet mods and instruct users to keep the original mod and remove neoforge-carpet-tick.
- Track upstream master and 1.20.1 version changes daily, synchronize documentation, and validate explicitly reviewed port rules before automatic releases. Unknown changes require review; documentation-only updates never change the release version.

- Publish the Forge JAR to GitHub Releases after a `tick_version` change passes the build and GameTests; unrelated pushes no longer publish a release.

### Changed

- Package the Minecraft 1.20.1 Forge `/tick` implementation as a lightweight server-side mod with version `1.4.112-tick-1.0.0` and artifact name `neoforge-carpet-1.4.112-tick-1.0.0.jar`.
- **Breaking:** Target Minecraft Forge 47.4.0 and later 47.4.x releases instead of NeoForge 47.1.x; servers must use Forge to load this mod.

### Fixed

- Allow Forge 47.4.0–47.4.19 to load the mod by lowering the minimum dependency version from 47.4.20 to 47.4.0. Compile against Forge 47.4.0 as the compatibility baseline.

### Removed

- Remove Carpet rules, Scarpet, other Carpet commands, and unrelated client features; only `/tick` is registered by this mod.

<!-- upstream-status:start -->
## Upstream tracking status

Source: [chililisoup/neoforge-carpet](https://github.com/chililisoup/neoforge-carpet). Detected versions are not a compatibility claim.

| Branch | Latest detected | Reviewed | Applied and verified | Status |
| --- | --- | --- | --- | --- |
| master | 1.4.147-port-1.0.8 (`44360a01d00b`) | Not verified | Not verified | informational-only |
| 1.20.1 | 1.4.112-port-1.0.8 (`4b3f3ddc7312`) | Not verified | Not verified | baseline-review-required |

Failure history: 2 distinct event(s). Details: `.github/upstream-state.json`; command test results: GitHub Actions artifacts.
<!-- upstream-status:end -->
