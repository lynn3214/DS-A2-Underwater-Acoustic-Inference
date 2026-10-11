# Decision Log

## 2026-10-12 — Freeze Phase 1 analysis design before outcome analysis

- Status: prospective, frozen before calculating observed paired differences.
- Decisions: user-authorized operational thresholds 3 dB primary and 1 dB sensitivity; two-sided alpha .05; one-sample t baseline; Newey-West Bartlett HAC with frozen bandwidth and correction; percentile MBB with frozen block selection and sensitivity; fixed IID and AR(1) simulation grids, replication counts, seeds, and decision rules. Full details are in `config/experiment_protocol.yaml` and `docs/analysis_plan.md`.
- Rationale: satisfy the Phase 1 task while avoiding outcome-informed methodological choices. The threshold choices are operational interpretations, not universal acoustic standards.
- Related commit: to be filled after commit succeeds.
- No NOAA day/night difference has been calculated as of this design record.

## 2026-10-10 — Freeze Phase 0 audit protocol before NOAA access

- Status: prospective decisions, not informed by dataset outcomes.
- Decisions: candidate SB02_13; local-clock windows 09:00–17:00 and 21:00–05:00; per-window 6/8 primary and 8/8 coverage-only eligibility; practical target of 30 paired dates; no outcome-based selection; unresolved time semantics block pairing; fallback sequence requires human approval.
- Rationale and provisional items: see `config/audit_protocol.yaml`.
- Related commit: to be populated only after the actual initial protocol commit succeeds.
- Note: no dataset has been accessed at the time of this entry.

## 2026-10-10 — Record Phase 0 source blockers (outcome-blind)

- Status: audit finding; no research outcome was examined.
- Finding: NOAA source timestamp labels do not define interval start/end/center; dataset-local timezone is unstated; companion brief JSON reports a 20 Hz lower frequency while the NCEI XML and CSV name indicate 10 Hz; no explicit redistribution license was verified.
- Consequence: no clock-window completeness or eligibility calculation was permitted. The initial protocol remains unchanged; no fallback dataset was selected.
- Related protocol commit: `aa4394b8474e24798096592870d0c22a1e52e00c`.
- Audit evidence: `results/audit/noaa_audit.json`, `results/audit/provenance.json`, and `docs/audit_report.md`.

## 2026-10-12 17:43 UTC — Phase 0.5 metadata resolution

- Status: prospective metadata interpretation; no effect outcomes examined.
- Direct source evidence: SB02_13 netCDF `time` and `time_stamp` comments specify start times for one-hour bins. Adopt `start` with high confidence.
- User specification: use `America/New_York`; preserve existing day/night windows and coverage criteria. Add a separate Phase 0.5 config so the frozen Phase 0 protocol remains intact.
- License resolution: exact product netCDF global license states free use and redistribution with a no-warranty/legal-use disclaimer. The small processed product and metadata snapshots may therefore be versioned; raw audio remains excluded.
- Unresolved: exact product brief JSON says 20–24,000 Hz, while the NCEI processing record and netCDF abstract/history say 10–24,000 Hz. Retain the discrepancy and require NOAA clarification.
- Related commit: this record and its evidence are included in the Phase 0.5 metadata-resolution commit; the exact SHA is reported in the final handoff.
- Evidence: `docs/metadata_resolution.md`, `results/audit/metadata_evidence.json`, and the updated `results/audit/noaa_audit.json`.
