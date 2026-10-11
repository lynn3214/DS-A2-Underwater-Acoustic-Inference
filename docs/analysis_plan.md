# Phase 1 Analysis Plan

## Question and scope

For eligible dates in the observed NOAA SanctSound SB02_13 deployment, estimate the average paired difference between the mean published hourly nighttime dB indicator and mean published hourly daytime dB indicator. This is observational and scoped to the eligible date process in this station deployment; it does not identify a causal effect of night or generalize automatically to other stations or years. Arithmetic means of dB indicators are not linear-energy means.

Each local date is one sampling unit. Day is `[09:00, 17:00)` and night is `[21:00, 05:00)` on the following date, attributed to the night start date. UTC start-of-bin labels are converted using `America/New_York`. Include a date only when each window has at least six valid hourly values. Full 8/8 coverage is a sensitivity description. Do not impute missing values or apply undocumented QC exclusions.

The estimand is `Delta = E[D_d]`, where `D_d = mean(night dB) - mean(day dB)`. The estimator is the arithmetic mean of eligible `D_d`. Test `H0: Delta=0` against two-sided `H1: Delta!=0` at alpha 0.05; report 95% intervals. Three dB is the pre-specified operational minimum meaningful effect and 1 dB is a secondary interpretation threshold. Neither is represented as a universal acoustic or ecological standard; compare their positions with estimates and uncertainty separately from statistical significance.

## Inference and simulations

Use a one-sample t interval/test as an IID baseline. HAC uses an intercept-only Newey-West estimator, Bartlett kernel, maximum lag `floor(4*(n/100)^(2/9))`, scalar finite-sample correction `n/(n-1)`, and a t reference with `n-1` df. Interpret its finite-sample calibration cautiously. The dependence-aware interval uses overlapping non-circular MBB blocks drawn uniformly with replacement, concatenated and truncated to `n`; primary length `ceil(n^(1/3))` and sensitivity lengths 2, 4, and 8. Use the 2.5th and 97.5th percentiles of bootstrap replicate means as the 95% interval. Do not derive a bootstrap p-value; the two-sided decision is whether that interval excludes zero.

All random work uses `numpy.random.default_rng` with seed root 20261012 and recorded child seeds. The empirical scale `sigma0` is the eligible paired-difference sample SD (`ddof=1`), solely a marginal simulation calibration. IID Gaussian sampling-distribution and power simulations use 5,000 replications per condition. Sampling-distribution conditions are `n={20,30,64}` and `Delta={0,3}`. Power is one-factor-at-a-time around `n=30`, `sigma=sigma0`, `Delta=3`, with the frozen grids in `config/experiment_protocol.yaml`; compare Monte Carlo rejection rates and Wilson intervals with noncentral-t analytical power. At zero effect, rejection is Type I error.

For controlled dependence, generate stationary Gaussian AR(1) series with stationary initialization, `rho={0,.3,.6,.9}`, `n=64`, `sigma=sigma0`, effects 0 and 3 dB, 2,000 independent series per condition and 999 bootstrap resamples per series. Compare IID t, HAC and MBB by Type I error, coverage, interval width and nonzero-effect rejection. These Monte Carlo `rho` values are known simulation truth, not estimates of NOAA dependence. Preserve all outcomes, including method failures.

Real-data diagnostics include a chronological time series and ACF at lags 1, 2, 3, 7, and 14 without bridging date gaps. Approximate white-noise bands are descriptive only. Never detrend, select a different dataset by outcome, or revise settings to improve results. Any deviation must be logged with timing and whether outcomes had been seen.

## Frozen design record

This plan and its machine-readable counterpart were frozen in Git before calculating real paired differences. See the commit history and `docs/decision_log.md`. Frequency metadata (10 vs 20 Hz lower bound) and absent row-level QC remain limitations. No causal interpretation is permitted.
