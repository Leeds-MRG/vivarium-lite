from typing import TYPE_CHECKING, Callable, List

import pandas as pd

if TYPE_CHECKING:
    # cyclic import
    from vivarium.framework.results.manager import ResultsManager


class ResultsInterface:
    """Builder interface for the results management system.

    The results management system allows users to delegate results production
    to the simulation framework. This process attempts to roughly mimic the
    groupby-apply logic commonly done when manipulating :mod:`pandas`
    DataFrames. The representation of state in the simulation is complex,
    however, as it includes information both in the population state table
    and dynamically generated information available from the
    :class:`value pipelines <vivarium.framework.values.Pipeline>`.
    Additionally, good encapsulation of simulation logic typically has
    results production separated from the modeling code into specialized
    `Observer` components. This often highlights the need for transformations
    of the simulation state into representations that aren't needed for
    modeling, but are required for the stratification of produced results.

    The purpose of this interface is to provide controlled access to a results
    backend by means of the builder object. It exposes methods
    to register stratifications, set default stratifications, and register
    results producers. There is a special case for stratifications generated
    by binning continuous data into categories.

    The expected use pattern would be for a single component to register all
    stratifications required by the model using :func:`register_default_stratifications`,
    :func:`register_stratification`, and :func:`register_binned_stratification`
    as necessary. A “binned stratification” is a stratification special case for
    the very common situation when a single continuous value needs to be binned into
    categorical bins. The `is_vectorized` argument should be True if the mapper
    function expects a DataFrame corresponding to the whole population, and False
    if it expects a row of the DataFrame corresponding to a single simulant.
    """

    def __init__(self, manager: "ResultsManager") -> None:
        self._manager: "ResultsManager" = manager
        self._name = "results_interface"

    @property
    def name(self) -> str:
        """The name of this ResultsInterface."""
        return self._name

    def set_default_stratifications(self, default_stratifications: List[str]):
        self._manager.set_default_stratifications(default_stratifications)

    # TODO: It is not reflected in the sample code here, but the “when” parameter should be added
    #  to the stratification registration calls, probably as a List. Consider this after observer implementation
    def register_stratification(
        self,
        name: str,
        categories: List[str],
        mapper: Callable = None,
        is_vectorized: bool = False,
        requires_columns: List[str] = (),
        requires_values: List[str] = (),
    ) -> None:
        """Register quantities to observe.

        Parameters
        ----------
        name
            Name of the of the column created by the stratification.
        categories
            List of string values that the mapper is allowed to output.
        mapper
            A callable that emits values in `categories` given inputs from columns
            and values in the `requires_columns` and `requires_values`, respectively.
        is_vectorized
            `True` if the mapper function expects a `DataFrame`, and `False` if it
            expects a row of the `DataFrame` and should be used by calling :func:`df.apply`.
        requires_columns
            A list of the state table columns that already need to be present
            and populated in the state table before the pipeline modifier
            is called.
        requires_values
            A list of the value pipelines that need to be properly sourced
            before the pipeline modifier is called.

        Returns
        ------
        None
        """
        self._manager.register_stratification(
            name,
            categories,
            mapper,
            is_vectorized,
            requires_columns,
            requires_values,
        )

    def register_binned_stratification(
        self,
        target: str,
        binned_column: str,
        bins: List = (),
        labels: List[str] = (),
        target_type: str = "column",
        **cut_kwargs,
    ) -> None:
        self._manager.register_binned_stratification(...)

    def register_observation(
        self,
        name: str,
        pop_filter: str = "",
        aggregator: Callable[[pd.DataFrame], float] = len,
        requires_columns: List[str] = None,
        requires_values: List[str] = None,
        additional_stratifications: List[str] = (),
        excluded_stratifications: List[str] = (),
        when: str = "collect_metrics",
    ) -> None:
        self._manager.register_observation(...)
