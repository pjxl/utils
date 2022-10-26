import math
import scipy.stats as st
import numpy as np
import pandas as pd


def confint(x, stat, se, ha='two-sided'):
    ci_lwr = x - stat * se
    ci_upr = x + stat * se
#     if ha[0] == 'l':
#         ci_lwr = None
#     else:
#         ci_lwr = x - stat * se
    
#     if ha[0] == 'r':
#         ci_upr = None
#     else:
#         ci_upr = x + stat * se

    return ci_lwr, ci_upr


# https://github.com/scipy/scipy/blob/47bb6febaa10658c72962b9615d5d5aa2513fa3a/scipy/stats/stats.py#L1330
def _ztest_p(z, ha):
    if ha == 'less':
        p = st.norm.cdf(z)
    elif ha == 'greater':
        p = st.norm.sf(z)
    elif ha == 'two-sided':
        p = 2 * st.norm.sf(abs(z))
        
    return p


def ztest_2prop(x_treat, n_treat, x_ctrl, n_ctrl, alpha=0.05, ha='two-sided'):
    """
    Conduct a two-proportion z-test.

    Parameters
    ----------
        x_treat: (numeric) The number of observations with the event of interest in the treatment group.

        n_treat: (numeric) The total number of observations in the treatment group.

        x_ctrl: (numeric) The number of observations with the event of interest in the control group.

        n_ctrl: (numeric) The total number of observations in the control group.

        alpha: (float; default=0.05) The desired significance level.

        ha: (string; default='two-sided') The desired directionality of the test. A valid input is one of ('two-sided', 'greater', 'less').
    """

    # Assert valid values for ha
    valid_ha = {'two-sided', 't', 'greater', 'g', 'less', 'l'}
    ha = ha.lower()

    # Raise an error if a valid ha value is not provided
    if ha not in valid_ha:
        raise ValueError('"ha" must be one of %r.' % valid_ha)

    # Calculate relative proportions
    p_treat = x_treat/n_treat
    p_ctrl = x_ctrl/n_ctrl
    p_pooled = (x_treat+x_ctrl)/(n_treat+n_ctrl)

    # Compute the standard error of the sampling distribution of the difference between p_treat and p_ctrl
    se = p_pooled*(1-p_pooled)*(1/n_treat+1/n_ctrl)
    se = math.sqrt(se)

    # Calculate the z test statistic
    z = (p_treat-p_ctrl)/se

    # Calculate the p-value associated with z
    p = _ztest_p(z, ha)

    # Calculate the critical z-score
    one_sided = ha in {'greater', 'less'}
    z_critical = st.norm.ppf(1 - alpha / (1 + (not one_sided)))

    # Find the lower and upper CIs boundaries
    # n.b.: in units of the difference between p_treat and p_ctrl
    ci_lwr, ci_upr = confint(p_treat-p_ctrl, z_critical, se, ha)

    # Calculate the pct lift
    lift = p_treat/p_ctrl-1
    lift_lwr = ci_lwr/p_ctrl
    lift_upr = ci_upr/p_ctrl

    # Function to format decimals as percentages for print-out readability
    # Optionally, prepend a sign (+/-) before a percentage (e.g., when representing lift estimates)
    def format_pct_str(x, precision=None, sign=False):
        pct = str(round(x*100, precision)) + '%'
        return '+' + pct if x >= 0 else pct

    # Star indicator if the diff in proportions was statsig
    sig = '*' if p <= alpha else ''

    # Print a readout of the experiment conclusion
    print(f'{format_pct_str(lift, precision=2)}',
        'lift in the treatment',
        f'({format_pct_str(1-alpha)} CI:',
        f'{format_pct_str(lift_lwr, precision=2, sign=True)}',
        f'to {format_pct_str(lift_upr, precision=2, sign=True)})',
        sig)

    # DataFrame with all test outputs of interest
    out_df = pd.DataFrame(
      {'': [p_ctrl, p_treat, z, p, lift, p_treat-p_ctrl, ci_lwr, ci_upr]},
      index=['control', 'treatment', 'z-score', 'p-value', 'lift', 'diff',
             'diff ({0:.0f}% CI lower)'.format(100*(1-alpha)),
             'diff ({0:.0f}% CI upper)'.format(100*(1-alpha))])

    with pd.option_context('display.precision', 10):
        return out_df


# https://github.com/scipy/scipy/blob/47bb6febaa10658c72962b9615d5d5aa2513fa3a/scipy/stats/stats.py#L5661
def _ttest_p(t, dof, ha):
    if ha == 'less':
        p = st.t.cdf(t, dof)
    elif ha == 'greater':
        p = st.t.sf(t, dof)
    elif ha == 'two-sided':
        p = 2 * st.t.sf(abs(t), dof)
        
    return p


def welch_ttest(treat, ctrl, alpha=0.05, ha='two-sided'):
    
    # Assert valid values for ha
    valid_ha = {'two-sided', 'greater', 'less'}
    ha = ha.lower()

    # Raise an error if a valid ha value is not provided
    if ha not in valid_ha:
        raise ValueError('"ha" must be one of %r.' % valid_ha)

    treat, ctrl = [pd.Series(i) for i in (treat, ctrl)]
    
    # Get each group's sample size 
    n_treat, n_ctrl = [i.count() for i in (treat, ctrl)]
    
    # Get the mean of each group
    mean_treat, mean_ctrl = [i.mean() for i in (treat, ctrl)]
    
    # Get the variance of each group
    var_treat, var_ctrl = [i.var(ddof=1) for i in (treat, ctrl)]
    
    # Calculate the pooled standard error
    se = var_treat/n_treat + var_ctrl/n_ctrl
    se = math.sqrt(se)
    
    t = (mean_treat-mean_ctrl) / se
    
    # Welch-Satterthwaite degrees of freedom    
    dof = (var_treat/n_treat + var_ctrl/n_ctrl)**2 / ((var_treat/n_treat)**2 / (n_treat-1) + (var_ctrl/n_ctrl)**2 / (n_ctrl-1))
    
    # Calculate the p-value associated with t and dof
    p = _ttest_p(t, dof, ha)
    
    # Calculate the critical t-score
    one_sided = ha in {'greater', 'less'}
    t_critical = st.t.ppf(1 - alpha / (1 + (not one_sided)), dof)
    
    # Find the lower and upper CIs boundaries
    # n.b.: in units of the difference between mean_treat and mean_ctrl
    ci_lwr, ci_upr = confint(mean_treat-mean_ctrl, t_critical, se, ha)
    
    # Calculate the pct lift
    lift = mean_treat/mean_ctrl-1
    lift_lwr = ci_lwr/mean_ctrl
    lift_upr = ci_upr/mean_ctrl
    
    # Function to format decimals as percentages for print-out readability
    # Optionally, prepend a sign (+/-) before a percentage (e.g., when representing lift estimates)
    def format_pct_str(x, precision=None, sign=False):
        pct = str(round(x*100, precision)) + '%'
        return '+' + pct if x >= 0 else pct

    # Star indicator if the diff in proportions was statsig
    sig = '*' if p <= alpha else ''

    # Print a readout of the experiment conclusion
    print(f'{format_pct_str(lift, precision=2)}',
        'lift in the treatment',
        f'({format_pct_str(1-alpha)} CI:',
        f'{format_pct_str(lift_lwr, precision=2, sign=True)}',
        f'to {format_pct_str(lift_upr, precision=2, sign=True)})',
        sig)

    # DataFrame with all test outputs of interest
    out_df = pd.DataFrame(
      {'': [mean_ctrl, mean_treat, t, p, dof, lift, mean_treat-mean_ctrl, ci_lwr, ci_upr]},
      index=['control', 'treatment', 't-score', 'p-value', 'DoF', 'lift', 'diff',
             'diff ({0:.0f}% CI lower)'.format(100*(1-alpha)),
             'diff ({0:.0f}% CI upper)'.format(100*(1-alpha))])

    with pd.option_context('display.precision', 10):
        return out_df

    
def f_score(precision, recall, beta=1):
    """
    Calculate the F-score for the given `precision`, `recall`, and `beta` values.

    Parameters
    ----------
        precision (float): The precision estimate, which must be a value in the range [0, 1].

        recall (float): The recall estimate, which must be a value in the range [0, 1].

        beta (int): The beta value to be used. Defaults to 1, in which case the return value is equivalent to the F1 score.
    """
    return (1+beta**2) * (precision*recall) / (beta**2*precision+recall)


def pop_prop_sample_size(d, p=0.5, N=None, cl=0.95):
    """
    Calculates the minimum sample size needed to estimate the proportion of observations within 
    a population that have a given characteristic, while meeting a given constraint on precision.

    When `N=None`, equivalent to `statsmodels.stats.proportion.samplesize_confint_proportion()`:
    https://www.statsmodels.org/dev/generated/statsmodels.stats.proportion.samplesize_confint_proportion.html

    For more information, see: https://online.stat.psu.edu/stat506/lesson/2/2.3

    Parameters:
        d : float in (0, 1)
            The required margin of error, or the half-length of the desired confidence interval.
        p : float in (0, 1), default 0.5
            Prior assumption around the proportion of the characteristic. Defaults to 0.5, which returns
            the most conservatively (large) sample size.
        N : int, default None
            The size of the population. When `None`, assume an infinite population, and ignore the finite
            population correction (fpc).
        cl : float in (0, 1), default 0.5
            The desired confidence level, defaulting to 0.95 or 95%.

    Returns:
        n : int
            The sample size needed to observe a population proportion as large as `p`, at confidence
            level `cl`, with a margine of error `d`. Round decimal values up to the nearest integer
            using `math.ceil()`.
    """

    # Calculate the alpha value
    alpha = 1-cl

    # Calculate the z-score
    z = st.norm.ppf(1-alpha/2)

    # If N is provided, assume a finite population and use the finite population correction
    if N:
        num = N*p*(1-p)
        denom = (N-1)*(d**2)/(z**2) + p*(1-p)
    # Otherwise, assume an infinite population
    else:
        num = z**2*p*(1-p)
        denom = d**2

    # Return sample size
    # Handle fractional sizes by returning the ceiling
    return math.ceil(num/denom)


def pop_prop_confint(p, n, cl=0.95):
    """
    Calculates the confidence interval for an estimate of a population proportion, using
    the normal approximation.

    Equivalent to `statsmodels.stats.proportion.proportion_confint()` using `method='normal'`.

    For more information, see: https://online.stat.psu.edu/stat506/lesson/2/2.2.

    Parameters
    ----------
        p : float in (0, 1)
            The observed proportion of observations in a sample having a given characteristic.
        n : int
            The number of observations in the sample.
        cl : float in (0, 1), default 0.5
            The desired confidence level, defaulting to 0.95 or 95%.

    Returns
    -------
        ci_low, ci_upper : tuple
            The lower and upper bounds of the confidence interval around `p`.
    """

    # Calculate the alpha value
    alpha = 1-cl

    # Calculate the z-score
    z = st.norm.ppf(1-alpha/2)

    # Calculate the variance in p
    var_p = p*(1-p)/n

    # Calculate the margin of error
    d = z*math.sqrt(var_p)

    return p - d, p + d