from collections import defaultdict
from typing import Callable, Dict, List, Tuple

import pandas as pd

from vivarium.framework.results.exceptions import ResultsConfigurationError
from vivarium.framework.results.stratification import Stratification


class ResultsContext:
    """
    Manager context for organizing observations and the stratifications they require.

    This context object is wholly contained by the manager :class:`vivarium.framework.results.manager.ResultsManger`.
    Stratifications can be added to the context through the manager via the
    :meth:`vivarium.framework.results.context.ResultsContext.add_observation` method.
    """

    def __init__(self):
        self._default_stratifications: List[str] = []
        self._stratifications: List[Stratification] = []
        # keys are event names
        # values are dicts with key (filter, grouper) value (measure, aggregator, additional_keys)
        self._observations = defaultdict(lambda: defaultdict(list))

    # noinspection PyAttributeOutsideInit
    def set_default_stratifications(self, default_grouping_columns: List[str]):
        if self._default_stratifications:
            raise ResultsConfigurationError(
                "Multiple calls are being made to set default grouping columns "
                "for results production."
            )
        if not default_grouping_columns:
            raise ResultsConfigurationError(
                "Attempting to set an empty list as the default grouping columns "
                "for results production."
            )
        self._default_grouping_columns = default_grouping_columns

    def add_stratification(
        self,
        name: str,
        sources: List[str],
        categories: List[str],
        mapper: Callable,
        is_vectorized: bool,
    ):
        """Add a stratification to the context.

        Parameters
        ----------
        name
            Name of the of the column created by the stratification.
        sources
            A list of the columns and values needed for the mapper to determinate
            categorization.
        categories
            List of string values that the mapper is allowed to output.
        mapper
            A callable that emits values in `categories` given inputs from columns
            and values in the `requires_columns` and `requires_values`, respectively.
        is_vectorized
            `True` if the mapper function expects a `DataFrame`, and `False` if it
            expects a row of the `DataFrame` and should be used by calling :func:`df.apply`.


        Returns
        ------
        None
        """
        if len([s.name for s in self._stratifications if s.name == name]):
            raise ValueError(f"Name `{name}` is already used")
        stratification = Stratification(name, sources, categories, mapper, is_vectorized)
        self._stratifications.append(stratification)

    def add_observation(
        self,
        name: str,
        pop_filter: str,
        aggregator: Callable[[pd.DataFrame], float],
        additional_stratifications: List[str] = (),
        excluded_stratifications: List[str] = (),
        when: str = "collect_metrics",
        **additional_keys: str,
    ):
        # TODO: _producers doesn't exist, stub code needs bugfix at observation implementation time
        groupers = self._get_groupers(additional_stratifications, excluded_stratifications)
        (
            self._producers[when][(pop_filter, groupers)].append(
                (name, aggregator, additional_keys)
            )
        )

    def gather_results(self, population: pd.DataFrame, event_name: str) -> Dict[str, float]:
        # Optimization: We store all the producers by pop_filter and groupers
        # so that we only have to apply them once each time we compute results.
        # TODO: uncomment and debug...
        # for stratification in self._stratifications:
        #     population = stratification(population)
        #
        # for (pop_filter, groupers), observations in self._observations[event_name].items():
        #     # Results production can be simplified to
        #     # filter -> groupby -> aggregate in all situations we've seen.
        #     pop_groups = self.population.query(pop_filter).groupby(list(groupers))
        #     for measure, aggregator, additional_keys in observers:
        #         aggregates = pop_groups.apply(aggregator)
        #         # Keep formatting all in one place.
        #         yield self._format_results(measure, aggregates, **additional_keys)
        ...

    def _get_groupers(
        self,
        additional_stratifications: List[str] = (),
        excluded_stratifications: List[str] = (),
    ) -> Tuple[str, ...]:
        groupers = list(
            set(self._default_stratifications) - set(excluded_stratifications)
            | set(additional_stratifications)
        )
        # Makes sure measure identifiers have fields in the same relative order.
        return tuple(sorted(groupers))

    @staticmethod
    def _format_results(
        measure: str, aggregates: pd.DataFrame, **additional_keys: str
    ) -> Dict[str, float]:
        results = {}
        # First we expand the categorical index over unobserved pairs.
        # This ensures that the produced results are always the same length.
        idx = pd.MultiIndex.from_product(
            aggregates.index.levels, names=aggregates.index.names
        )
        data = pd.Series(data=0, index=idx)
        data.loc[aggregates.index] = aggregates

        def _format(field, param):
            """Format of the measure identifier tokens into FIELD_param."""
            return f"{str(field).upper()}_{param}"

        for params, val in data.iteritems():
            key = "_".join(
                [_format("measure", measure)]
                + [_format(field, measure) for field, param in zip(data.index.names, params)]
                # Sorts additional_keys by the field name.
                + [
                    _format(field, measure)
                    for field, param in sorted(additional_keys.items())
                ]
            )
            results[key] = val
        return results
