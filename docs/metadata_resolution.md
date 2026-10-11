# Phase 0.5 Metadata Resolution Decision

**Decision date:** 2026-10-12 Asia/Singapore  
**Assessment:** **CONDITIONAL PASS** for feasibility screening. This decision authorizes no Phase 1 work.

## Sources consulted

- Exact dataset NCEI landing record: https://www.ncei.noaa.gov/access/metadata/landing-page/bin/iso?id=gov.noaa.ncei.pad:NOAA-Navy-SanctSound_SB02_13_BB_1h
- Exact dataset NOAA bucket listing: https://storage.googleapis.com/noaa-passive-bioacoustic/?prefix=sanctsound/products/sound_level_metrics/sb02/sanctsound_sb02_13_bb_1h/
- Exact dataset netCDF: https://storage.googleapis.com/noaa-passive-bioacoustic/sanctsound/products/sound_level_metrics/sb02/sanctsound_sb02_13_bb_1h/data/SanctSound_SB02_13_BB_1h.nc
- Exact dataset brief metadata: https://storage.googleapis.com/noaa-passive-bioacoustic/sanctsound/products/sound_level_metrics/sb02/sanctsound_sb02_13_bb_1h/metadata/SanctSound_SB02_13_BB_1h-metadata.json
- Exact dataset ERDDAP attributes request attempted: https://coastwatch.pfeg.noaa.gov/erddap/griddap/noaaSanctSound_SB02_13_BB_1h.das
- User-specified related broadband product: https://coastwatch.pfeg.noaa.gov/erddap/griddap/noaaSanctSound_MB02_04_BB_1h.html
- User-specified related Stellwagen PSD product: https://coastwatch.pfeg.noaa.gov/erddap/griddap/noaaSanctSound_SB02_15_PSD_1h.graph
- Official sound-level processing software directory consulted: https://github.com/MarineBioAcousticsRC/Triton/tree/master/Remoras/Soundscape-Metrics

Machine-readable evidence and direct metadata attribute extracts are in [`results/audit/metadata_evidence.json`](../results/audit/metadata_evidence.json). The exact dataset ERDDAP request returned HTTP 403 with an IP blacklist response. Related-product metadata is treated as corroboration only.

## Evidence and interpretation

**Timestamp:** The exact SB02_13 netCDF file has a `time.comment` and `time_stamp.comment` attribute stating “Start time of 1 hour bin over which sound pressure levels are calculated.” This is direct product-specific evidence. Confidence in start-time labeling: **high**. Related products use the same convention, but they are not needed to establish the primary interpretation.

**Time zone:** `America/New_York` was specified in the user’s Phase 0.5 instruction and is consistent with the station coordinates in NCEI metadata. All source timestamps are UTC and were converted with aware datetimes and Python `zoneinfo`. This deployment does not cross either 2020-11-01 fall-back or 2021-03-14 spring-forward. Synthetic tests separately verify both transitions.

**Frequency band:** The exact netCDF global abstract/history, the NCEI processing description, and the CSV column `BB_10-24000` state 10–24,000 Hz. The exact product’s brief JSON `DATA_QUALITY` field states 20–24,000 Hz. Because both claims are product-specific and conflict, the operational band remains unresolved pending NOAA clarification. The majority of direct product fields is evidence for 10–24,000 Hz, not grounds to erase the conflict.

**Reuse:** The exact netCDF global `license` attribute says the data may be used and redistributed for free and includes a no-warranty/legal-use disclaimer. This exact-product statement permits redistribution for this project. It is not identified as a Creative Commons or OSI license. The processed CSV, netCDF, XML and JSON metadata files are included; raw acoustic recordings are not.

## Coverage results

Using `America/New_York`, start-time labels, and the predeclared clock windows:

- Dates screened: 66 local calendar dates.
- `>=6/8` valid hours in **each** day and night window: 64 eligible paired dates.
- `8/8` in **each** window: 64 eligible paired dates.
- Both criteria have one contiguous eligible run of 64 dates, 2020-11-23 through 2021-01-25; both exceed the practical 30-date screen.
- The first date has 5 day and 8 night hours; the final date has 3 day and 0 night hours. Both are excluded by both rules.
- Among represented hourly bins, the source has zero missing/invalid records by local hour and local date. Partial calendar-date endpoints are deployment boundaries, not internal data gaps.

These calculations count valid hourly indicators only. No day/night SPL values were compared, and no daily differences, estimates, intervals, tests, or power were computed. Since the direct timestamp evidence is high confidence, a one-hour-shift sensitivity calculation was not required by the conditional instruction.

## Limitations and decision

The exact dataset has no row-level QC field or documented quantitative filtering threshold. Its brief JSON also conflicts with its netCDF and NCEI processing description on the lower frequency bound. The one-deployment scope remains narrow, and 64 dates do not by themselves guarantee inferential validity under serial dependence.

**Feasibility decision: CONDITIONAL PASS.** Timestamp interpretation, timezone conversion, coverage, and continuity pass the Phase 0.5 screen. Resolve the frequency metadata discrepancy with NOAA and carry the QC limitation into the design review before Phase 1. Researcher approval of the provisional 3 dB minimum meaningful effect and future inference settings remains necessary. Stop here for independent review.
