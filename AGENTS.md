# AGENTS.md — DS-A2 Research Repository

## 1. Mission and authority

This repository is for **DS-A2 | Inference and Uncertainty Notebook**, Data Science course, 2026.

Primary official course source: https://tjluo-ucas.github.io/ds/
Submission platform: https://learn.spaiq.ai/
Deadline from the provided assignment: **2026-10-14 16:30 Asia/Shanghai**. The platform timestamp is authoritative.

Follow, in order: (1) current DS-A2 task text and official course instructions, (2) official course website, (3) official dataset documentation, (4) this `AGENTS.md`, (5) specific user prompts. If requirements conflict, stop and describe the conflict; do not silently invent rules or change the research question.

The assessed work requires:
1. Predefine research question, estimand, hypotheses, and minimum meaningful effect.
2. Simulate a statistic's sampling distribution.
3. Implement an appropriate bootstrap, permutation, or parametric interval/test.
4. Examine power as sample size, noise, and effect change.
5. Construct an assumption-violating counterexample and explain changed conclusions.

Deliverables include an executable notebook with fixed seeds, method derivation/note, interval/effect/power figures, counterexample results, PDF, AI verification log, and versioned GitHub repository with code, raw results, provenance, and reproduction instructions. Platform submission also requires a 150–300-word summary and a stable repository URL with commit/tag. Do not claim submission was completed unless verified.

## 2. Working environment and execution

- Work **inside the repository root**. Create subdirectories/files as needed; do not expect a pre-existing structure.
- Use the existing Conda environment **`nussem1`** for every Python/data/notebook/test command. In noninteractive shells initialize Conda first, for example:

  ```bash
  source "$(conda info --base)/etc/profile.d/conda.sh"
  conda activate nussem1
  python -c "import sys; print(sys.executable)"
  ```

- Verify the active interpreter is from `nussem1` **before** doing Python work. If `conda` or `nussem1` is unavailable, report the blocker. **Do not silently use base/system Python or create another environment.**
- Before installing any dependency, inspect the environment and explain what is missing. Prefer existing packages; do not install or upgrade without explicit permission.
- Record Python, Conda, OS, relevant packages/versions, random seeds, and dataset provenance. For eventual notebooks, ensure top-to-bottom execution from a clean kernel without hidden state.
- Never commit secrets, personal data, credentials, large generated caches, or redundant raw audio. Respect source terms and GitHub file-size restrictions.

## 3. Research plan — current status

**Status: proposed design, not validated by data.** The initial audit is strictly a *feasibility audit*, not the final analysis.

Working title: *Day–Night Variability in Underwater Sound Levels: Statistical Inference, Power, and Temporal Dependence*.

Primary candidate: NOAA SanctSound, Stellwagen Bank, **SB02_13**, hourly broadband sound-pressure-level product. Starting metadata DOI: https://doi.org/10.25921/yyt5-g930 . Verify actual download files, exact column names, units, time conventions, QC, and license from official NOAA metadata—never assume them.

Primary scientific question: For the specified station/deployment and clock-defined windows, what is the average within-date night-minus-day difference in hourly broadband SPL (dB), and how uncertain is the estimate? This is an observational contrast, **not** a causal claim about nighttime or acoustic sources.

Proposed windows, in the station's confirmed local time zone:
- **Day:** 09:00 inclusive to 17:00 exclusive (8 hourly bins).
- **Night:** 21:00 inclusive to next-day 05:00 exclusive (8 hourly bins); assign this night to its starting calendar date.
- Pair a day window with the night window starting on the same local calendar date. Exclude incomplete deployment-boundary dates according to the predeclared coverage criteria.
- Confirm the semantics of hourly timestamps (start/end/center) and DST before generating any pairing. If ambiguous, do not guess.

Proposed per-date statistic: `D_d = mean(hourly_dB in night_d) - mean(hourly_dB in day_d)`. These are arithmetic means of the **published hourly dB indicators**; not linear acoustic-energy means. Proposed estimand: `Delta = E[D_d]` for the specified station/period and eligible observational process. Explicitly state that generalization beyond that scope requires additional assumptions.

Proposed inferential hypothesis: `H0: Delta = 0`, two-sided `H1: Delta != 0`, nominal `alpha = 0.05`; 95% intervals. Candidate minimum meaningful effect `delta_min = 3 dB` is **provisional**, not a universal acoustic standard or a justified claim about energy doubling. A possible 1 dB vs 3 dB interpretation sensitivity analysis is secondary. Researcher must approve/freeze the meaningful-effect threshold with rationale **before confirmatory outcome analysis**.

## 4. Precommitted feasibility-audit rules

These are rules to document before inspecting outcome contrasts; they are **not claims that the dataset passes**:

- Main coverage criterion: at least **6 valid hourly indicators out of 8** in **each** paired day and night window. Also report **8/8** eligibility as coverage-only sensitivity, without testing day/night effects.
- Target: at least **30 eligible paired dates** as a *practical screening threshold*, not a theorem guaranteeing valid inference.
- Prefer to evaluate contiguous eligible-date runs when assessing autocorrelation and moving-block bootstrap feasibility. Track gaps and do not implicitly bridge them in lag calculations.
- If fewer than 30 eligible dates, or continuity/QC/timezone requirements fail: record the trigger and recommend a **predefined metadata-based fallback search**, first for another suitable deployment at the same station, then another SanctSound station. Selection must use only coverage, measurement compatibility, timestamps, quality, and provenance—not effect size, p-values, or a visually promising day–night difference. Audit must **not autonomously switch the designated primary dataset**; obtain approval before substitution.
- Audit diagnostics may examine marginal SPL distributions, completeness, date coverage, and serial dependence. **Do not compute, plot, or report outcome comparisons, estimates of `Delta`, confidence intervals, p-values, or significance during the audit.** Do not calculate the observed paired differences except when formally authorized for the subsequent analysis stage.
- Audit report should separate: verified facts, observed audit metrics, assumptions, and unresolved issues.

## 5. Planned methods for later phases (DO NOT RUN IN INITIAL AUDIT)

Once the audit is reviewed and the design is frozen:
- Paired-date inference: mean of `D_d`; IID one-sample t interval/test as a **baseline**, not automatically valid under temporal dependence.
- Dependence-aware main comparison: HAC/Newey–West standard error on an intercept-only mean model; document the lag/bandwidth and finite-sample convention before execution.
- Secondary sensitivity: moving block bootstrap (MBB), operating on **contiguous** daily differences with a documented block-selection rule. Proposed starting heuristic `block_length = ceil(n**(1/3))` is *not* presumed optimal; methods and limitations must be validated through simulations. Avoid crossing missing-date gaps.
- Simulation of sampling distribution: IID Gaussian daily-difference model and fixed RNG seeds. Predefine the simulation noise **calibration rule**, not its numerical outcome: `sigma0 = sample standard deviation (ddof=1) of eligible daily paired differences` once the researcher authorizes analysis. This is a marginal scale, **not** a long-run standard deviation or an IID SE justification.
- Power: vary sample size, marginal noise, and effect, comparing Monte Carlo results (with uncertainty) against the exact noncentral-t analytical power **only under the matching IID Gaussian model**. Check type-I error when true effect is zero.
- Assumption-violating counterexample: stationary AR(1) daily-difference sequences, `D_t = Delta + eps_t`, `eps_t = rho*eps_(t-1) + u_t`, `u_t ~ N(0, sigma**2*(1-rho**2))` and stationary initialization. Compare nominal vs empirical CI coverage/type-I error and power under IID t, HAC, and MBB, acknowledging all methods' finite-sample limitations. Simulated `rho` is controlled truth; empirical ACF estimates are **not** known truth.
- Keep research inference and controlled-method-validation simulations clearly separated. No causal attribution and no claim of external generality unsupported by data.

## 6. Integrity and change control

- **Before downloading or examining data**, create an initial Git commit recording `AGENTS.md`, the approved audit protocol/config, and the audit instructions. Include the actual commit SHA in the audit report. If Git configuration or commit fails, disclose the obstacle and request direction before accessing data. Never invent a commit or claim that Git timestamps are tamper-proof.
- All subsequent changes to definitions, eligibility, methods, or planned parameters must be logged in `docs/decision_log.md` with reason, time, and related commit. Distinguish prospective changes from changes prompted by observed outcomes.
- Retain meaningful failed runs, negative results, and challenges to the proposed claims in `docs/experiment_log.md` and versioned small raw-result artifacts. Avoid committing enormous temporary logs; summarize and preserve diagnostic evidence.
- Record AI tool and task, accepted/rejected recommendations, human review, and independent verification in `docs/ai_use_log.md`. Do not invent human verification or mark checks complete without actual evidence.
- Do not fabricate data, numerical results, source details, experiments, citations, execution, or tests. Label each result **verified**, **expected**, **assumed**, or **proposed**.
- Run/tests only when authorized by the current stage. Report actual commands, interpreter paths, artifacts and failure messages. Use deterministic seeds for simulation; record hash and URL for externally downloaded source data.

## 7. Engineering and documentation standards

- Keep code modular, minimal, readable, and testable. Prefer `pathlib`; avoid absolute machine-specific paths. Keep original downloaded files immutable when possible.
- Save source URLs, retrieval date, metadata snapshots, size, and SHA-256 checksums. Preserve official QC flags and use documented filtering rules.
- Create only necessary files for the current phase. Eventual planned structure may include `config/`, `data/raw/`, `data/processed/`, `src/`, `notebook/`, `results/raw/`, `results/figures/`, `docs/`, and `tests/`.
- In reports, distinguish verified dataset facts from interpretations and assumptions. Numerical claims must be traceable to saved computation outputs.
- When an issue is unresolved (DST, missing flags, hour bin semantics, dataset access, insufficient samples), report it explicitly and do not paper over it.

## 8. Stop conditions and response format

For initial audit work, **stop after producing audit artifacts and an audit decision recommendation**. Do **not** implement the final inferential notebook, conduct hypothesis tests, choose an outcome-favorable dataset, or export a final submission PDF.

At completion report concisely: environment verification, initial Git commit SHA, data provenance/checksum, audit checks performed, artifacts created, pass/fail/uncertain per criterion, limitations, and explicit questions requiring human approval before formal inference.
