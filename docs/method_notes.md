# Phase 1 Method Notes

## Observed statistic

For eligible local date `d`, let `\bar{Y}_{d,day}` and `\bar{Y}_{d,night}` be the arithmetic means of the published hourly sound-level dB indicators in the day `[09:00,17:00)` and night `[21:00,05:00)` windows, respectively (night is assigned to its starting date). The daily observation is `D_d = \bar{Y}_{d,night} - \bar{Y}_{d,day}`. With n eligible dates, the target estimate is the mean of the eligible `D_d` values. This is an observational within-date contrast. An arithmetic mean of published dB indicators is not the mean linear acoustic energy transformed back to dB.

## IID one-sample t baseline

Let `s^2 = sum((D_d - mean(D))^2)/(n-1)`. The standard error is `s/sqrt(n)`; the 95% interval is `mean(D) +/- t_(0.975,n-1)*s/sqrt(n)`. The two-sided test uses `t=mean(D)/(s/sqrt(n))`. Exact small-sample t calibration requires independent Gaussian daily differences; independence is not guaranteed by a contiguous date series.

A 95% confidence interval describes the long-run coverage of the stated procedure under its assumptions; it does not mean that a fixed `Delta` has 95% probability of lying in this realized interval. An interval containing zero does not establish that `Delta=0`.

## Newey-West HAC

For demeaned residuals `e_t`, use Bartlett weights `w_k=1-k/(L+1)` and `gamma_k=n^-1 sum_(t=k+1)^n e_t e_(t-k)`. The long-run variance estimate is `gamma_0 + 2 sum_(k=1)^L w_k gamma_k`. The variance of the mean divides this by n and applies scalar correction `n/(n-1)`. The frozen rule is `L=floor(4*(n/100)^(2/9))`, which gives L=3 at n=64. The interval uses a t reference with n−1 degrees of freedom as frozen. This is an asymptotic approximation; size and bandwidth sensitivity at n=64 are limitations.

## Moving block bootstrap

For block length b, enumerate overlapping non-circular blocks of b consecutive dates. Draw blocks uniformly with replacement, concatenate, truncate to n, and calculate the bootstrap mean. The 95% interval uses the empirical 2.5th and 97.5th percentiles from 1,999 bootstrap means. Primary `b=ceil(n^(1/3))=4`; compare b=2 and b=8. The interval's exclusion of zero defines the two-sided decision; no bootstrap p-value is calculated. This approximate dependence method has finite-sample and block-selection uncertainty.

## IID sampling and power simulations

Generate independent `Normal(Delta,sigma^2)` daily observations using `numpy.random.default_rng`. Set `sigma0` to the observed eligible-difference sample SD (ddof=1) as a marginal scale calibration only. Use 5,000 replications per condition. Hold the two-sided t decision fixed. Analytical power is the probability that a noncentral t variate with df n−1 and noncentrality `Delta*sqrt(n)/sigma` falls outside the two-sided central t critical values. Wilson intervals quantify Monte Carlo rate uncertainty. At Delta=0 the rejection rate estimates Type I error.

## Dependence counterexample

Generate stationary Gaussian AR(1) daily values using `epsilon_0~N(0,sigma^2)` and `epsilon_t=rho*epsilon_(t-1)+u_t`, with `u_t~N(0,sigma^2*(1-rho^2))`; set `D_t=Delta+epsilon_t`. Across 2,000 independent series per rho/effect condition, compare t, HAC, and MBB intervals and decisions. The rho values are known simulation truth, not values inferred from the NOAA ACF. Report rates with Wilson intervals. The results show that all selected methods can miscalibrate under strong dependence.
