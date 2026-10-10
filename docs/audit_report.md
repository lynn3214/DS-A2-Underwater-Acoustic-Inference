# Phase 0 NOAA Feasibility Audit

**Status:** audit completed with an unresolved design blocker. No Phase 1 work is authorized by this report. The protocol commit was created before source access: `aa4394b8474e24798096592870d0c22a1e52e00c`.

## Verified source facts

- NOAA NCEI identifies DOI `10.25921/yyt5-g930` as broadband SPL at 1-hour resolution for SanctSound SB02_13, Stellwagen Bank; the observation period is 2020-11-22 through 2021-01-26. The NCEI record gives the precise extent as 2020-11-22 17:20 UTC to 2021-01-26 17:00 UTC.
- The NCEI processing description says 10–24,000 Hz, hourly values are the median of at least 1,800 one-second values, and units are dB re 1 µPa. The CSV column name is `BB_10-24000`.
- The companion brief JSON has a conflicting quality entry, `Frequency (Hz): 20 to 24000`. This discrepancy needs resolution before measurement compatibility is treated as fully verified.
- CSV timestamps carry a `Z` suffix and are whole-hour UTC labels. The metadata describes one-hour resolution but does not say whether a label denotes interval start, end, or center. The local time zone is not named in the dataset metadata.
- NOAA/NCEI documents visual/acoustic quality assessment, but the CSV has no QC column and metadata gives no row-level quality flag or quantitative exclusion rule. Metadata provides liability and citation constraints, but no explicit open license or redistribution grant was found.

Sources: [NCEI dataset landing page](https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncei.pad:NOAA-Navy-SanctSound_SB02_13_BB_1h), [official NOAA public bucket listing](https://storage.googleapis.com/noaa-passive-bioacoustic/?prefix=sanctsound/products/sound_level_metrics/sb02/sanctsound_sb02_13_bb_1h/). Exact source URLs, retrieval time, object generations, sizes, and checksums are in [`provenance.json`](../results/audit/provenance.json). Local XML and brief JSON snapshots are retained under `data/raw/` but are Git-ignored because redistribution rights are not explicit.

## Observed audit metrics

Computed by [`src/audit_noaa.py`](../src/audit_noaa.py), saved in [`noaa_audit.json`](../results/audit/noaa_audit.json). The CSV contains 1,560 parsed records and 1,560 finite values, from 2020-11-22 17:00 UTC to 2021-01-26 16:00 UTC. Records are strictly hourly across this span: no duplicate timestamps, nonmonotonic adjacent rows, cadence gaps, or non-hour-aligned labels were observed. There are 65 records at each UTC hour; the first and last UTC dates are partial (7 and 17 records respectively), while intermediate UTC dates have 24 records.

Overall SPL values (without day/night comparison) range from 87.726289 to 117.738856 dB; median 103.172739 dB. The IQR screen flagged 31 values for review only; no values were removed. The hourly lag-1 correlation among 1,559 adjacent hourly pairs is 0.7416. This is an overall hourly-series diagnostic and does not replace the planned daily-difference dependence assessment.

**Window coverage and eligibility counts were deliberately not computed.** Without documented hourly label semantics, assigning rows to clock windows would be an unsupported choice. Therefore the >=6/8 counts, >=8/8 counts, eligible paired-date count, and contiguous eligible-date run lengths remain unknown; the practical >=30-date screen cannot be evaluated yet. No paired differences, day/night comparisons, effect estimates, intervals, p-values, or power were computed.

## Gate table

| Criterion | Status | Evidence / blocker |
|---|---|---|
| Official provenance and licensing/redistribution clarity | UNCERTAIN | NOAA NCEI DOI and matching official bucket source verified; explicit reuse/redistribution license not located. |
| Download/reacquisition reproducibility and checksum | PASS | Public 57,449-byte CSV and official metadata snapshots retrieved; hashes, exact object URLs, GCS generations, ETags, and retrieval time recorded. |
| Timestamp, timezone, DST, hourly-bin interpretation | FAIL | UTC representation is explicit, but bin label semantics are undocumented; local time zone is not stated in the source metadata. Do not pair windows. |
| Valid measurement and QC documentation | UNCERTAIN | Units and processing are described; row-level QC absent; companion JSON frequency band conflicts with NCEI XML/CSV. |
| >=6/8 and >=8/8 coverage, with >=30 date screen | UNCERTAIN | Not evaluated because bin semantics and source-local clock mapping are unresolved. No eligibility counts are claimed. |
| Missingness and contiguous runs for dependence-aware analysis | UNCERTAIN | Hourly record is gap-free; 65 UTC days represented with partial first/last UTC dates. Eligible-date runs cannot be determined before valid window assignment. |
| Suitability of predeclared clock-defined scientific question | UNCERTAIN | The question is operationally clear, but the source does not establish how to map hourly labels to local clock-hour bins. |

## Reproduction and tests

Python work used the existing `nussem1` environment. Verified interpreter: `/Users/jinshenhui/miniforge3/envs/nussem1/bin/python`; Python 3.10.18; Conda 25.9.1; PyYAML 6.0.2; macOS 15.5 arm64. No random seeds were needed because the audit is deterministic and contains no simulation.

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate nussem1
python -m unittest discover -s tests -v
python src/audit_noaa.py
```

All 8 synthetic-only unit tests passed on the final run. The first run had one failed synthetic coverage fixture, which was corrected; the initial failure is preserved in `docs/experiment_log.md`. Tests cover half-open boundaries, cross-midnight night assignment, valid-hour counts, DST-aware conversion, unknown timestamp semantics, run segmentation, duplicate/invalid timestamps, and separate 6/8 versus 8/8 coverage thresholds. Tests use no NOAA outcomes.

## Recommendation and required review

**Do not advance this dataset to confirmatory analysis yet.** Request a NOAA/NCEI metadata clarification for (1) timestamp interval labeling, (2) the 10 Hz versus 20 Hz lower band discrepancy, (3) station local timezone if official confirmation is required, and (4) applicable redistribution terms. Once timestamp semantics and timezone are confirmed, re-run only the coverage portion under the frozen rules; if fewer than 30 paired dates or essential QC/time criteria fail, propose the predeclared metadata-only fallback sequence for human approval. The primary dataset must not be switched autonomously.

Before Phase 1, the researcher must also approve and justify the provisional 3 dB meaningful-effect threshold and freeze inferential/simulation settings. This report stops at the Phase 0 audit gate and awaits review and explicit authorization.
