# Experiment Log

## Phase 0 initialization

- Date: 2026-10-10 (client date; exact retrieval times will be recorded in UTC).
- Status: protocol setup only; no NOAA dataset has been accessed or examined.
- Planned audit command and outcomes: pending actual execution.
- Failures and negative evidence: pending; record actual errors and limitations here without fabricating results.
- No inferential analysis, power analysis, paired differences, or counterexample simulation is authorized in Phase 0.

## 2026-10-10 — NOAA source audit

- Initial source access followed protocol commit `aa4394b8474e24798096592870d0c22a1e52e00c`.
- Retrieved the 57,449-byte processed CSV and two official metadata objects; see `results/audit/provenance.json` for URLs, retrieval time, generations, and SHA-256 hashes.
- Executed `python -m unittest discover -s tests -v` in `nussem1`. First run: 7 passed, 1 failed because the synthetic UTC fixture did not map to the expected local clock windows; this was a fixture construction error. Corrected fixture and reran: all 8 passed.
- Executed `python src/audit_noaa.py` in `nussem1`; outcome-blind metrics are in `results/audit/noaa_audit.json`.
- Negative/unresolved evidence: hourly bin-label semantics absent; local time zone absent from source metadata; frequency lower bound differs in companion brief JSON; no explicit open redistribution license found; no row-level QC flags. Per protocol, window eligibility and date counts were not computed.
- No effect, inferential interval/test, power, or counterexample experiment was run.
