import numpy as np
import pandas as pd
import pytest

from vivarium.framework.utilities import (
    from_yearly,
    handle_exceptions,
    import_by_path,
    rate_to_probability
)


def test_from_yearly():
    one_month = pd.Timedelta(days=30.5)
    rate = 0.01
    new_rate = from_yearly(rate, one_month)
    assert round(new_rate, 5) == round(0.0008356164383561645, 5)


def test_rate_to_probability():
    rate = np.array([0.001])
    prob = rate_to_probability(rate)
    assert np.isclose(prob, 0.00099950016662497809)


def test_import_class_by_path():
    cls = import_by_path("collections.abc.Set")
    from collections.abc import Set

    assert cls is Set


def test_import_function_by_path():
    func = import_by_path("vivarium.framework.utilities.import_by_path")
    assert func is import_by_path


def test_bad_import_by_path():
    with pytest.raises(ImportError):
        import_by_path("junk.garbage.SillyClass")
    with pytest.raises(AttributeError):
        import_by_path("vivarium.framework.components.SillyClass")


class CustomException(Exception):
    pass


@pytest.mark.parametrize("test_input", [KeyboardInterrupt, RuntimeError, CustomException])
def test_handle_exceptions(test_input):
    def raise_me(ex):
        raise ex

    with pytest.raises(test_input):
        func = handle_exceptions(raise_me(test_input), None, False)
        func()
