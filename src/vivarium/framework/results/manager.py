from collections import Counter
from enum import Enum
from typing import TYPE_CHECKING, Callable, List, Union

import pandas as pd

from vivarium.framework.event import Event
from vivarium.framework.results.context import ResultsContext

if TYPE_CHECKING:
    # Cyclic import
    from vivarium.framework.engine import Builder


class SourceType(Enum):
    COLUMN = 0
    VALUE = 1


class ResultsManager:
    """Backend manager object for the results management system.

    The :class:`ResultManager` actually performs the actions needed to
    stratify and observe results. It contains the public methods used by the
    :class:`ResultsInterface` to register stratifications and observations,
    which provide it with lists of methods to apply in their respective areas.
    It is able to record observations at any of the time-step sub-steps
    (`time_step__prepare`, `time_step`, `time_step__cleanup`, and
    `collect_metrics`).
    """

    def __init__(self):
        self._metrics = Counter()
        self._results_context = ResultsContext()
        self._required_columns = {"tracked"}
        self._required_values = set()
        self._name = "results_manager"

    @property
    def name(self) -> str:
        """The name of this ResultsManager."""
        return self._name

    @property
    def metrics(self):
        return self._metrics.copy()

    # noinspection PyAttributeOutsideInit
    def setup(self, builder: "Builder"):
        self.population_view = builder.population.get_view([])
        self.clock = builder.time.clock()
        self.step_size = builder.time.step_size()

        builder.event.register_listener("time_step__prepare", self.on_time_step_prepare)
        builder.event.register_listener("time_step", self.on_time_step)
        builder.event.register_listener("time_step__cleanup", self.on_time_step_cleanup)
        builder.event.register_listener("collect_metrics", self.on_collect_metrics)

        self.get_value = builder.value.get_value

        builder.value.register_value_modifier("metrics", self.get_results)

    def on_time_step_prepare(self, event: Event):
        self.gather_results("time_step__prepare", event)

    def on_time_step(self, event: Event):
        self.gather_results("time_step", event)

    def on_time_step_cleanup(self, event: Event):
        self.gather_results("time_step__cleanup", event)

    def on_collect_metrics(self, event: Event):
        self.gather_results("collect_metrics", event)

    def gather_results(self, event_name: str, event: Event):
        population = self._prepare_population(event)
        for results_group in self._results_context.gather_results(population, event_name):
            self._metrics.update(results_group)

    def set_default_stratifications(self, default_stratifications: List[str]):
        self._results_context.set_default_stratifications(default_stratifications)

    def register_stratification(
        self,
        name: str,
        categories: List[str],
        mapper: Callable,
        is_vectorized: bool,
        requires_columns: List[str] = (),
        requires_values: List[str] = (),
    ) -> None:
        """Manager-level stratification registration, including resources and the stratification itself.

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
        target_columns = list(requires_columns) + list(requires_values)
        self._results_context.add_stratification(
            name, target_columns, categories, mapper, is_vectorized
        )
        self._add_resources(requires_columns, SourceType.COLUMN)
        self._add_resources(requires_values, SourceType.VALUE)

    def register_binned_stratification(
        self,
        target: str,
        target_type: str,
        binned_column: str,
        bins: List[Union[int, float]],
        labels: List[str],
        **cut_kwargs,
    ) -> None:
        """Manager-level registration of a continuous `target` quantity to observe into bins in a `binned_column`.

        Parameters
        ----------
        target
            String name of the state table column or value pipeline used to stratify.
        target_type
            "column" or "value"
        binned_column
            String name of the column for the binned quantities.
        bins
            List of scalars defining the bin edges, passed to :meth: pandas.cut. Lists
            `bins` and `labels` must be of equal length.
        labels
            List of string labels for bins. Lists `bins` and `labels` must be of equal length.
        **cut_kwargs
            Keyword arguments for :meth: pandas.cut.

        Returns
        ------
        None
        """

        def _bin_data(data: pd.Series) -> pd.Series:
            return pd.cut(data, bins, labels=labels, **cut_kwargs)

        if len(bins) != len(labels):
            raise ValueError(
                f"Bin length ({len(bins)}) does not match labels length ({len(labels)})"
            )
        target_arg = "required_columns" if target_type == "column" else "required_values"
        target_kwargs = {target_arg: [target]}
        self.register_stratification(
            binned_column, bins, _bin_data, is_vectorized=True, **target_kwargs
        )

    def register_observation(
        self,
        name: str,
        pop_filter: str,
        aggregator_sources: List[str],
        aggregator: Callable,
        requires_columns: List[str] = None,
        requires_values: List[str] = None,
        additional_stratifications: List[str] = (),
        excluded_stratifications: List[str] = (),
        when: str = "collect_metrics",
    ) -> None:
        self._results_context.add_observation(
            name,
            pop_filter,
            aggregator_sources,
            aggregator,
            additional_stratifications,
            excluded_stratifications,
            when,
        )
        self._add_resources(requires_columns, SourceType.COLUMN)
        self._add_resources(requires_values, SourceType.VALUE)

    def _add_resources(self, target: List[str], target_type: SourceType):
        if not len(target):
            return  # do nothing on empty lists
        target = set(target) - {"event_time", "current_time", "step_size"}
        if target_type == SourceType.COLUMN:
            self._required_columns.update(target)
        elif target_type == SourceType.VALUE:
            self._required_values.update(self.get_value(target))

    def _prepare_population(self, event: Event):
        population = self.population_view.subview(list(self._required_columns)).get(
            event.index
        )
        population["current_time"] = self.clock()
        population["step_size"] = event.step_size
        population["event_time"] = self.clock() + event.step_size
        for k, v in event.user_data.items():
            population[k] = v
        for pipeline in self._required_values:
            population[pipeline.name] = pipeline(event.index)
        return population

    def get_results(self, index, metrics):
        # Shim for now to allow incremental transition to new results system.
        metrics.update(self.metrics)
        return metrics
