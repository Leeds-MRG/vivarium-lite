"""
====================
The Artifact Manager
====================

This module contains the :class:`ArtifactManager`, a ``vivarium`` plugin
for handling complex data bound up in a data artifact.

"""
import re
from pathlib import Path
from typing import Any, Sequence, Union

import pandas as pd
from loguru import logger

from vivarium.config_tree import ConfigTree
from vivarium.framework.artifact.artifact import Artifact

_Filter = Union[str, int, Sequence[int], Sequence[str]]


class ArtifactManager:
    """The controller plugin component for managing a data artifact."""

    configuration_defaults = {
        "input_data": {
            "artifact_path": None,
            "artifact_filter_term": None,
            "input_draw_number": None,
        }
    }

    def _load_artifact(self, configuration: ConfigTree) -> Union[Artifact, None]:
        """Looks up the path to the artifact hdf file, builds a default filter,
        and generates the data artifact. Stores any configuration specified filter
        terms separately to be applied on loading, because not all columns are
        available via artifact filter terms.

        Parameters
        ----------
        configuration :
            Configuration block of the model specification containing the input data parameters.

        Returns
        -------
            An interface to the data artifact.
        """
        if not configuration.input_data.artifact_path:
            return None
        artifact_path = parse_artifact_path_config(configuration)
        base_filter_terms = get_base_filter_terms(configuration)
        logger.debug(f"Running simulation from artifact located at {artifact_path}.")
        logger.debug(f"Artifact base filter terms are {base_filter_terms}.")
        logger.debug(f"Artifact additional filter terms are {self.config_filter_term}.")
        return Artifact(artifact_path, base_filter_terms)

    def __repr__(self):
        return "ArtifactManager()"


# class ArtifactInterface:
#     """The builder interface for accessing a data artifact."""
#
#     def __init__(self, manager):
#         self._manager = manager
#
#     def load(self, entity_key: str, **column_filters: Union[_Filter]) -> pd.DataFrame:
#         """Loads data associated with a formatted entity key.
#
#         The provided entity key must be of the form
#         {entity_type}.{measure} or {entity_type}.{entity_name}.{measure}.
#
#         Here entity_type denotes the kind of entity being described. Examples
#         include cause, risk, population, and covariates.
#
#         The entity_name is the name of the specific entity. For example,
#         if we had entity_type as cause, we might have entity_name as
#         diarrheal_diseases or ischemic_heart_disease.
#
#         Finally, measure is the name of the quantity the data describes.
#         Examples of measures are incidence, disability_weight, relative_risk,
#         and cost.
#
#         Parameters
#         ----------
#         entity_key
#             The key associated with the expected data.
#         column_filters
#             Filters that subset the data by a categorical column and then
#             remove the column from the raw data. They are supplied as keyword
#             arguments to the load method in the form "column=value".
#
#         Returns
#         -------
#         pandas.DataFrame
#             The data associated with the given key filtered down to the requested subset.
#         """
#         return self._manager.load(entity_key, **column_filters)
#
#     def __repr__(self):
#         return "ArtifactManagerInterface()"

def get_base_filter_terms(configuration: ConfigTree):
    """Parses default filter terms from the artifact configuration."""
    base_filter_terms = []

    draw = configuration.input_data.input_draw_number
    if draw is not None:
        base_filter_terms.append(f"draw == {draw}")

    return base_filter_terms


def parse_artifact_path_config(config: ConfigTree) -> str:
    """Gets the path to the data artifact from the simulation configuration.

    The path specified in the configuration may be absolute or it may be relative
    to the location of the configuration file.

    Parameters
    ----------
    config
        The configuration block of the simulation model specification containing the artifact path.

    Returns
    -------
    str
        The path to the data artifact.
    """
    path = Path(config.input_data.artifact_path)

    if not path.is_absolute():

        path_config = config.input_data.metadata("artifact_path")[-1]
        if path_config["source"] is None:
            raise ValueError("Insufficient information provided to find artifact.")
        path = Path(path_config["source"]).parent.joinpath(path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"Cannot find artifact at path {path}")

    return str(path)
