# Decision Log

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
