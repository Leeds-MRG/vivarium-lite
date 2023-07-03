"""
===========================
Framework Utility Functions
===========================

Collection of utility functions shared by the ``vivarium`` framework.

"""
import functools
from importlib import import_module
from typing import Any, Callable

import numpy as np


def from_yearly(value, time_step):
    return value * (time_step.total_seconds() / (60 * 60 * 24 * 365.0))


def rate_to_probability(rate):
    # encountered underflow from rate > 30k
    # for rates greater than 250, exp(-rate) evaluates to 1e-109
    # beware machine-specific floating point issues
    rate[rate > 250] = 250.0
    return 1 - np.exp(-rate)


def import_by_path(path: str) -> Callable:
    """Import a class or function given it's absolute path.

    Parameters
    ----------
    path:
      Path to object to import
    """

    module_path, _, class_name = path.rpartition(".")
    return getattr(import_module(module_path), class_name)

