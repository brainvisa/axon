# Changelog

## [6.0.12] 2026-05-21

### Added

- BIDS `participants.tsv` file is supported in BV databases

### Changed

- Capsul processes in Axon improvements and fixes
- A few misc. fixes

## [6.0.10] 2026-03-06

### Changed

- fixed the software update check
- fixed the doc web paged displayed when an update is available


## [6.0.8] 2026-02-27

### Changed

- make `brainvisa --shell` work again
- copydata process: avoid errors in output_databse link: use only valid databases

## [6.0.5] 2026-02-06

### Changed

- `brainvisa --setup` updates all builtin databases, not only the first (main) one
- read-only databases are now hidden for selecting outputs
- fixed a possible crash in parameters change notifications when triggered from a non-principal thread (like a process execution)

## [6.0.0] 2026-01-12

### Added

- The Morphologist pipeline has been added a summary report process step, and some global morphometry which may be used as QC with normative values.
- A new snapshot utility process is available, which is a simpler version of the former "SnapBase" tool, which had been removed in 5.1 versions because its maintenance was discontinued. The new process is named "snapbase", as a replacement.
- The BIDS files organization for Morphologist has been widely changed, in order to fit more standard BIDS schemas, and fix problems in the earlier version. For this reason, data processed with the former (1.0) BIDS schema will not be reusable with the newer one (2.0).


```{raw} html
:file: ../../doc/en/help/changelog.html
```

