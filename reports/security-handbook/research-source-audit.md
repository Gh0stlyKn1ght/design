# Published research source review

The handbook now includes a teaching adaptation of six public ROS2X Research case studies by Juan Carlos Nevarez (@Gh0stlyKn1ght). The reviewed public revision is `30ce3dd0eb22b384f010e5f9679e459517be6965`. The case studies support implementation-specific threat and evidence discussions; they do not change the handbook's six-pass, one-inconclusive runtime result.

## Checksum reconciliation needed

A read-only check recomputed all 152 entries in the six published case checksum manifests. **146 entries matched; six did not.** Every mismatch is a case `README.md`. The listed logs, captures, harness sources and other evidence files matched their recorded hashes.

All six recorded README hashes match their versions immediately before public commit `e3985a8`, which added architecture diagrams and editorial material. The current READMEs were changed without corresponding checksum updates. This accounts for the observed drift; it does not justify reporting all current published checksums as passing.

The historical manifests have not been modified. A dated reconciliation that identifies the original manifest, pinned source commit, current README hashes and editorial change is needed before describing the current source bundle as fully checksum-verified. `research-source-review.json` records the observed hashes and the history comparison.

The CVE-2023-39948 manifest also retains `release_status: reviewed` even though the case is present in the public repository and the source registry records external publication. Reconcile this metadata through the same versioned process.

## Scope of this review

The review read published case documentation and recomputed file hashes. It did not rerun the experiments, validate a current dependency inventory, or reassess vendor patch coverage. No private research record, raw evidence, withheld case or manuscript text was copied into the handbook.
