# Phase 1 Parameter Mapping

`config/experiment_protocol.yaml` is the frozen design record. The Phase 1 runner currently reads the NOAA input path, expected source SHA-256, analysis timezone, and simulation seed root from YAML. It does not yet load every numerical grid or setting dynamically; changing YAML alone will not change all runner behavior.

The following effective values are fixed in `src/run_phase1.py` (or the called procedure defaults) and were checked against the frozen YAML and saved output artifacts by `tests/test_protocol_consistency.py`:

- Eligibility minimum: 6 valid hours per window; strict eligibility is 8/8 (from `src/inference.py`'s default).
- Operational thresholds: 3 dB and 1 dB; IID/HAC alpha and interval level: 0.05/95%.
- HAC bandwidth formula and MBB block-length sensitivity `[2, 4, 8]`; MBB resamples: 1,999; MBB seeds are root seed plus block length.
- Daily ACF lags `[1, 2, 3, 7, 14]`.
- IID sampling grid: n `[20, 30, 64]`, effects `[0, 3]`, 5,000 replications per condition.
- IID power one-factor grids: n `[10, 20, 30, 40, 60]`, noise multipliers `[0.5, 1, 1.5, 2]`, effects `[0, 1, 2, 3, 4, 5]`, 5,000 replications per condition; reference settings n=30, effect=3 dB.
- AR(1) counterexample: rho `[0, 0.3, 0.6, 0.9]`, effects `[0, 3]`, n=64, 2,000 series per condition, 999 bootstrap replicates per series.
- AR(1) generator diagnostic: 30,000 series of length 100 per rho, using the called function's defaults; it is a generator check rather than an experiment condition.
- Seed offsets beyond `seed_root` are assigned in source in a deterministic order. The result CSV/JSON records per-condition and per-series seeds where applicable.

The consistency test validates that the checked-in outputs' grid values, replication counts, seed root, observed sample mean, and IID t interval/p-value agree with the frozen YAML and saved daily data. It does not prove that arbitrary future YAML edits will be consumed by the runner. Moving all duplicated parameters into configuration would be a separate code change and is not part of this QA pass.
