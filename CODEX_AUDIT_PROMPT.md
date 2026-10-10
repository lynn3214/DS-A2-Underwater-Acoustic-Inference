# Codex task — DS-A2 Phase 0: NOAA dataset feasibility audit ONLY

You are operating inside the **empty DS-A2 repository root**. The user created only this root directory. `AGENTS.md` is located directly in that root. **Read it fully and follow it.** Create all required subdirectories, scripts, configs, tests, and documentation yourself. Do not assume any other existing files.

## Goal and scope

Execute a **reproducible feasibility audit**, **not** the final DS-A2 statistical analysis, for NOAA SanctSound hourly broadband SPL at Stellwagen Bank station/deployment **SB02_13**, starting from official DOI: https://doi.org/10.25921/yyt5-g930 . Establish whether the data can support a predeclared within-date clock-defined day–night inference. Do not calculate the actual day–night effect, confidence interval, p-value, or power yet. Do not create the final assignment notebook or submission PDF at this stage.

The user wants to review this audit with ChatGPT before authorizing implementation. Do not proceed beyond the audit gate.

## Mandatory runtime

Every Python execution, script, test, and package inspection must use the **existing** Conda environment `nussem1`:

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate nussem1
which python
python -c "import sys; print(sys.executable)"
```

If `conda` is not initialized, locate its supported initialization script and activate it. If the environment is absent, stop and report the blocker; do not use another Python, create an environment, or install/upgrade packages without approval. Use shell utilities as appropriate. Record the Python/Conda paths and versions.

## Step 1 — establish the frozen pre-data record

1. Read `AGENTS.md`, inspect Git status, and verify you are in the intended root.
2. Create only the minimum directories initially needed (`config/`, `docs/`, `src/`, `tests/`, `results/audit/`, `data/raw/` as justified).
3. Write `config/audit_protocol.yaml` (or JSON if YAML tooling is unavailable), including:
   - Candidate dataset DOI, station/product, immutable-source strategy, and explicit provenance validation steps.
   - Clock-defined daytime 09:00–17:00 and nighttime 21:00–next day 05:00 in confirmed **local station time**; night assigned to starting date. Both are half-open windows.
   - Complete-date screening criterion >=6/8 valid hourly values separately in both windows; also coverage-only >=8/8 diagnostic.
   - Target of >=30 eligible paired dates, and a requirement to assess uninterrupted stretches separately.
   - No effect-based dataset selection, no day–night contrast computed during the audit.
   - Missingness/QC and DST/hour-bin ambiguity handling; if unresolved, flag as a blocker, never silently guess.
   - If `n<30`, a staged fallback proposal based only on official metadata, coverage and quality: another compatible deployment at the same site, then a compatible SanctSound site; require human approval before changing.
   - Proposed future (not executed now) `sigma0 = sample SD of eligible daily paired differences (ddof=1)`; proposed MBB heuristic `ceil(n**(1/3))`, to be reviewed after the audit; future HAC and Monte Carlo configuration to be frozen before outcome analysis.
   - Provisional meaningful-effect threshold 3 dB; 1/3 dB interpretation sensitivity possible. No claim of acoustic consensus without a source.
   - The reason each rule is chosen, along with which decisions remain provisional.
4. Create `docs/decision_log.md`, `docs/experiment_log.md`, `docs/ai_use_log.md`, a minimal `.gitignore`, and a short `README.md` explaining Phase 0 and reproduction. Do not initialize a second Git repository inside an existing one.
5. **Before retrieving or inspecting actual data**, make an initial Git commit with `AGENTS.md`, config, audit protocol, this audit prompt if present in the root, and initial documentation. Record the resulting commit SHA in the final report. If a Git commit is impossible (e.g., identity missing), describe what is needed and **stop before data access**. Do not invent timestamps or SHA.

## Step 2 — verify official source and acquire minimum necessary data

1. Open the NOAA DOI and official landing/metadata documents; verify station identifier, observation period, product definition, frequency band, units, quality flags, licensing, timestamp semantics and actual CSV/netCDF download links. Prefer official NOAA domains rather than third-party rehosts.
2. Download the **smallest practical relevant processed-hourly dataset** for the audit; do **not** download large raw WAV/audio archives. If the official link or API is not accessible, report the exact URL/HTTP error and stop or propose an alternative official path. Do not fabricate local data to claim audit completion.
3. Save an immutable original file under `data/raw/` if licensing and repository size allow. Otherwise document its official acquisition path and checksum; do not commit huge binary files to ordinary Git. Save a source metadata snapshot or a structured provenance manifest with retrieval datetime, exact URLs, file names, size, SHA-256, official citations/DOI, and QC notes.
4. Record data license/redistribution uncertainty explicitly; do not infer reuse rights from public availability.

## Step 3 — implement and run audit code

Create small, readable scripts inside `src/` (for example `src/audit_noaa.py`, `src/time_windows.py`) plus focused tests inside `tests/`. Keep paths repository-relative and parameterize all site/window choices from `config/audit_protocol.yaml` or JSON.

Compute **only non-outcome audit diagnostics**:

- Input schema, parse success, units, timestamp representation, duplicated or nonmonotonic timestamps, sampling cadence, gross invalid values and QC flags according to official rules.
- Deployment date range and actual valid-hour counts by day and hour of local time; day/night **completeness** separately, without comparing SPL magnitudes between them.
- Counts of dates eligible by >=6/8 and >=8/8 rules; counts excluded by each reason; deployment boundary losses.
- Missingness by date/hour and contiguous eligible-date run lengths. Treat gaps as breaks for daily-lag diagnostics; report the longest run.
- Marginal hourly SPL distribution (overall, not contrasting day/night outcomes), possible outliers for investigation without automatic removal.
- Overall hourly-series dependence diagnostics only where legitimate (ACF after accounting for gaps/regular sampling). You may describe a plan for **paired daily-difference ACF**, but **do not compute paired differences in this audit**.
- Timezone and DST validation, including if time stamps represent interval start, end, or center. If source ambiguity prevents trustworthy windows, report an unresolved blocker rather than manufacturing a pairing.

Implement targeted tests for window boundaries, cross-midnight assignment, hour-count rules, duplicate/invalid timestamp handling, and missing-date-run segmentation using **synthetic fixtures only**. Do not confuse fixture results with real-data findings.

Save versioned machine-readable results (`results/audit/*.json` or small CSV), a handful of diagnostic figures if relevant (`results/audit/figures/`), and a human-readable `docs/audit_report.md`. The report must link diagnostic numbers/figures to specific scripts and output files and label all findings by verification status. Preserve meaningful failures and negative results in `docs/experiment_log.md`.

## Step 4 — decision gate and handoff

Provide a compact audit decision table with **PASS / FAIL / UNCERTAIN** for:
1. Official provenance and licensing/redistribution clarity.
2. Download/reacquisition reproducibility and checksum.
3. Timestamp, timezone, DST, and hourly-bin interpretation.
4. Valid measurement and QC documentation.
5. >=6/8 and >=8/8 coverage, with >=30 date screening.
6. Missingness and contiguous runs for dependence-aware analysis.
7. Suitability of the predeclared clock-defined scientific question.

If eligibility is under 30 or essential quality criteria fail, suggest a **non-outcome-based** fallback sequence and stop pending approval. If the dataset seems feasible, recommend proceeding to design freeze **but still stop**. Do not choose the 3 dB cutoff using observed contrasts; do not perform inferential tests, power simulations, AR(1) counterexample, or final notebook/PDF export.

## Required final response to the user

Report:
- exact commands used for `nussem1` verification and audit execution;
- initial protocol commit SHA and any later audit-result commit SHA (only if real);
- exact source URLs, provenance identifier(s), retrieval date, source hashes, and source/version caveats;
- generated files and how to reproduce the audit;
- the gate table and unresolved blockers;
- any failures, negative evidence, or deviations with reasons;
- explicit request for review and authorization before Phase 1.

**Do not claim that any script was executed, dataset downloaded, Git committed, or test passed unless it actually happened.**
