"""
==========================
Vivarium Testing Utilities
==========================

Utility functions and classes to make testing ``vivarium`` components easier.

"""
import numpy as np
import pandas as pd


def build_table(value, year_start, year_end, columns=("age", "year", "sex", "value")):
    value_columns = columns[3:]
    if not isinstance(value, list):
        value = [value] * len(value_columns)

    if len(value) != len(value_columns):
        raise ValueError("Number of values must match number of value columns")

    rows = []
    for age in range(0, 140):
        for year in range(year_start, year_end + 1):
            for sex in ["Male", "Female"]:
                r_values = []
                for v in value:
                    if v is None:
                        r_values.append(np.random.random())
                    elif callable(v):
                        r_values.append(v(age, sex, year))
                    else:
                        r_values.append(v)
                rows.append([age, age + 1, year, year + 1, sex] + r_values)
    return pd.DataFrame(
        rows,
        columns=["age_start", "age_end", "year_start", "year_end", "sex"]
        + list(value_columns),
    )
