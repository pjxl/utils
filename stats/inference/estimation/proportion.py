import math
import scipy.stats as st
import numpy as np
import numpy.typing as npt
from typing import Union, Tuple


def sample_size(
    moe: float, prop: float=0.5, popl_size: int=None, alpha: float=0.05
    ) -> int:
    """
    Calculates the minimum sample size needed to estimate the proportion of observations within 
    a population that have a given characteristic, while meeting a given constraint on precision.

    Parameters
    ----------
        moe : float in (0, 1)
            The desired margin of error, or the half-length of the desired confidence interval.
        prop : float in (0, 1), default 0.5
            Prior assumption around the proportion of the characteristic. Defaults to 0.5, which returns
            the most conservatively (large) sample size.
        popl_size : int, default None
            The size of the population. When `None`, assume an infinite population, and ignore the finite
            population correction (FPC).
        alpha : float in (0, 1), default 0.5
            The desired alpha level (1 - confidence level), defaulting to 0.05, i.e a 95% CL.

    Returns
    -------
        n : int
            The sample size needed to observe a population proportion as large as `prop`, at alpha
            level `alpha`, with a margin of error `moe`. Round decimal values up to the nearest integer
            using `math.ceil()`.

    Notes
    -----
    Validated against: https://www.statskingdom.com/50_ci_sample_size.html
    
    When `popl_size=None`, equivalent to `statsmodels.stats.proportion.samplesize_confint_proportion()`:
    https://www.statsmodels.org/dev/generated/statsmodels.stats.proportion.samplesize_confint_proportion.html

    References
    ----------
    .. [*] https://online.stat.psu.edu/stat506/lesson/2/2.3

    """

    # Find critical value (z-score)
    cv = st.norm.ppf(1-alpha/2)

    # If N is provided, assume a finite population and use the finite population correction
    if popl_size:
        num = popl_size*prop*(1-prop)
        denom = (popl_size-1)*(moe**2)/(cv**2) + prop*(1-prop)
    # Otherwise, assume an infinite population
    else:
        num = cv**2*prop*(1-prop)
        denom = moe**2

    # Return sample size
    # Handle fractional sizes by returning the ceiling
    return math.ceil(num/denom)


def confint(
    prop: float, sample_size: int, alpha: float=0.05
    ) -> Tuple[float]:
    """
    Calculates the confidence interval for an estimate of a population proportion, using
    the normal approximation.

    Parameters
    ----------
        prop : float in (0, 1)
            The observed proportion of observations in a sample having a given characteristic.
        sample_size : int
            The number of observations in the sample.
        alpha : float in (0, 1), default 0.5
            The desired alpha level (1 - confidence level), defaulting to 0.05, i.e a 95% CL.

    Returns
    -------
        ci_lower, ci_upper : tuple of floats
            The lower and upper bounds of the confidence interval around `prop`.

    Notes
    -----
    Validated against: https://www.statskingdom.com/proportion-confidence-interval-calculator.html
    
    Equivalent to `statsmodels.stats.proportion.proportion_confint()` using `method='normal'`.
    
    TODO: Incorporate additional esimation methods, e.g. Clopper-Pearson and especially Wilson score interval. 

    References
    ----------
    .. [*] https://online.stat.psu.edu/stat506/lesson/2/2.2
    """

    # Find critical value (z-score)
    cv = st.norm.ppf(1-alpha/2)

    # Find variance in p
    var = prop*(1-prop)/sample_size

    # Find margin of error
    moe = cv*math.sqrt(var)

    # Find lower and upper bounds of CI
    ci_lower, ci_upper = prop-moe, prop+moe

    return ci_lower, ci_upper


def strat_proportion(
    props: Union[npt.NDArray[np.float64], 'pd.Series[np.float64]'], 
    strat_sizes: Union[npt.NDArray[np.int64], 'pd.Series[np.int64]']
    ) -> np.float64:
    """
    Calculate the weighted proportion within a stratified sample.

    Parameters
    ----------
        props : array-like of floats
            The proportions observed in each sample.
        strat_sizes : array-like of ints
            The number of observations in each stratum, whose grand total equals the size of the population.

    Returns
    -------
        p : float
            The weighted proportion across the entire stratified sample.

    Notes
    -----

    References
    ----------
    .. [*] Lohr, S.: "Sampling: Design and Analysis", 2nd ed., ch. 3 (93-95)
    .. [*] https://stattrek.com/survey-research/stratified-sampling-analysis
    """
    
    # Find total population size
    popl_size = np.sum(strat_sizes)
    
    # Find sampling fraction (stratum weights)
    weights = strat_sizes/popl_size

    return np.sum(weights*props)


def strat_confint(
    props: Union[npt.NDArray[np.float64], 'pd.Series[np.float64]'], 
    sample_sizes: Union[npt.NDArray[np.int64], 'pd.Series[np.int64]'], 
    strat_sizes: Union[npt.NDArray[np.int64], 'pd.Series[np.int64]'], 
    alpha: float=0.05
    ):
    """
    In a stratified sample setting, calculates the confidence interval for an estimate of a population proportion.

    Parameters
    ----------
        props : array-like of floats
            The proportions observed in each sample.
        sample_sizes : array-like of ints
            The sample size of each stratum.
        strat_sizes : array-like of ints
            The number of observations in each stratum, whose grand total equals the size of the population.
    	alpha : float in (0, 1), default 0.5
            The desired alpha level (1 - confidence level), defaulting to 0.05, i.e a 95% CL.

    Returns
    -------
        ci_lower, ci_upper : tuple
            The lower and upper bounds of the confidence interval around the (weighted) sample proportion.

    Notes
    -----

    References
    ----------
    .. [*] Lohr, S.: "Sampling: Design and Analysis", 2nd ed., ch. 3 (93-95)
    .. [*] https://stattrek.com/survey-research/stratified-sampling-analysis
    """

    # Find critical value (z-score)
    cv = st.norm.ppf(1-alpha/2)

    # Find total population size
    popl_size = np.sum(strat_sizes)

    # Find weighted sample proportion
    prop = strat_proportion(props, strat_sizes)
    
    # Find variance of each stratum proportion
    var = sample_sizes/(sample_sizes-1) * props * (1-props)

    # Find standard error
    se = np.sqrt(np.sum(strat_sizes**2 * (1/popl_size)**2 * (1-sample_sizes/strat_sizes) * var/sample_sizes))

    # Find margin of error
    moe = cv*se

    # Find lower and upper bounds of CI
    ci_lower, ci_upper = prop-moe, prop+moe

    return ci_lower, ci_upper
