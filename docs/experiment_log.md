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

## 2026-10-12 — Phase 0.5 metadata and coverage follow-up

- Environment: existing `nussem1`, Python 3.10.18, Conda 25.9.1, h5py 3.14.0, PyYAML 6.0.2.
- Retrieved the exact SB02_13 netCDF from the same NOAA object prefix; size 132,286 bytes, SHA-256 `6f9f0211a98f415cd2c26526ec7bae9788bc3401b5ad707b7a9a7882609fba03`.
- Direct netCDF attribute inspection verified both time coordinate comments identify one-hour-bin starts and the exact product global license permits free redistribution with disclaimers. Prior licensing uncertainty is resolved for repository inclusion.
- Tried exact SB02_13 ERDDAP `.das`; NOAA returned HTTP 403 stating this request IP is on its blacklist. This failed access is preserved in `results/audit/metadata_evidence.json`.
- The two related NOAA ERDDAP products independently say their time coordinates are bin starts; logged as indirect corroboration only.
- Under `America/New_York` with start-label semantics, the audit found 64 eligible dates under both 6/8 and 8/8 rules, in one uninterrupted run; the 30-date screen is met. Local date/hour missingness has no internal gaps.
- Unresolved negative finding: exact SB02_13 brief JSON reports 20–24,000 Hz, while its netCDF abstract/history, NCEI processing record, and CSV variable label report 10–24,000 Hz. No frequency/outcome values were used to choose a preferred timestamp convention.
- No observed day–night contrasts, intervals, tests, power, or simulations were computed.
- First Phase 0.5 test run: 12 passed, 1 failed because the synthetic missing-hour fixture removed the earliest timestamp, outside the audit's source-span missingness denominator. Moved the synthetic omission to an interior date; the final rerun passed all 13 tests.
