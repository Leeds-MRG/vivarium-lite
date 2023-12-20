"""
==========================
Vivarium Interactive Tools
==========================

This module provides an interface for interactive simulation usage. The main
part is the :class:`InteractiveContext`, a sub-class of the main simulation
object in ``vivarium`` that has been extended to include convenience
methods for running and exploring the simulation in an interactive setting.

See the associated tutorials for :ref:`running <interactive_tutorial>` and
:ref:`exploring <exploration_tutorial>` for more information.

"""
from math import ceil
from typing import Any, Callable, Dict, List

import pandas as pd

from vivarium.framework.engine import SimulationContext
from vivarium.framework.time import Time, Timedelta
from vivarium.framework.values import Pipeline

from .utilities import log_progress, run_from_ipython


class InteractiveContext(SimulationContext):
    """A simulation context with helper methods for running simulations interactively."""

    def __init__(self, *args, setup=True, **kwargs):
        super().__init__(*args, **kwargs)

        if setup:
            self.setup()

    @property
    def current_time(self) -> Time:
        """Returns the current simulation time."""
        return self._clock.time

    def setup(self):
        super().setup()
        self.initialize_simulants()

    def step(self, step_size: Timedelta = None):
        """Advance the simulation one step.

        Parameters
        ----------
        step_size
            An optional size of step to take. Must be the same type as the
            simulation clock's step size (usually a pandas.Timedelta).
        """
        old_step_size = self._clock.step_size
        if step_size is not None:
            if not isinstance(step_size, type(self._clock.step_size)):
                raise ValueError(
                    f"Provided time must be an instance of {type(self._clock.step_size)}"
                )
            self._clock._step_size = step_size
        super().step()
        self._clock._step_size = old_step_size

    def run_for(self, duration: Timedelta, with_logging: bool = True) -> int:
        """Run the simulation for the given time duration.

        Parameters
        ----------
        duration
            The length of time to run the simulation for. Should be the same
            type as the simulation clock's step size (usually a pandas
            Timedelta).
        with_logging
            Whether or not to log the simulation steps. Only works in an ipython
            environment.

        Returns
        -------
        int
            The number of steps the simulation took.

        """
        time = self._clock.time + duration
        iterations = int(ceil((time - self._clock.time) / self._clock.step_size))

        if run_from_ipython() and with_logging:
            for _ in log_progress(range(iterations), name="Step"):
                self.step(None)
        else:
            for _ in range(iterations):
                self.step(None)
        assert self._clock.time - self._clock.step_size < time <= self._clock.time
        return iterations

    def get_population(self, untracked: bool = False) -> pd.DataFrame:
        """Get a copy of the population state table.

        Parameters
        ----------
        untracked
            Whether or not to return simulants who are no longer being tracked
            by the simulation.

        """
        return self._population.get_population(untracked)

    def get_value(self, value_pipeline_name: str) -> Pipeline:
        """Get the value pipeline associated with the given name."""
        return self._values.get_value(value_pipeline_name)

    def __repr__(self):
        return "InteractiveContext()"
