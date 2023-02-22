"""
===========================
Framework Utility Functions
===========================

Collection of utility functions shared by the ``vivarium`` framework.

"""

import numpy as np


def rate_to_probability(rate):
    # encountered underflow from rate > 30k
    # for rates greater than 250, exp(-rate) evaluates to 1e-109
    # beware machine-specific floating point issues
    rate[rate > 250] = 250.0
    return 1 - np.exp(-rate)
