# Changelog

## [Unreleased]

### Changed

- `brainvisa --setup` updates all builtin databases, not only the first (main) one

## [6.6.0] 2026-01-12

### Added

- The Morphologist pipeline has been added a summary report process step, and some global morphometry which may be used as QC with normative values.
- A new snapshot utility process is available, which is a simpler version of the former "SnapBase" tool, which had been removed in 5.1 versions because its maintenance was discontinued. The new process is named "snapbase", as a replacement.
- The BIDS files organization for Morphologist has been widely changed, in order to fit more standard BIDS schemas, and fix problems in the earlier version. For this reason, data processed with the former (1.0) BIDS schema will not be reusable with the newer one (2.0).


```{raw} html
:file: ../../doc/en/help/changelog.html
```

