# DS-A2 Phase 0: NOAA Feasibility Audit

This repository is at Phase 0 only. The audit assesses whether NOAA SanctSound
hourly broadband SPL data for Stellwagen Bank SB02_13 can support the proposed
clock-defined paired-date design. It must not calculate or report the day–night
contrast, inferential intervals, tests, power, or counterexample simulations.

The frozen protocol is in `config/audit_protocol.yaml`. The protocol was
committed before any NOAA data access. Read `docs/audit_report.md` for the
eventual audit outcome and blockers. No Phase 1 work should begin until human
review and authorization.

## Reproduction

Use the existing Conda environment `nussem1`. After source metadata and the
processed hourly input have been acquired and provenance recorded, run the
repository audit entry point described in `docs/audit_report.md`. Do not fetch
raw acoustic audio. Raw source files are excluded from Git; preserve their
official URL, retrieval time, size, and SHA-256 in the provenance record.
