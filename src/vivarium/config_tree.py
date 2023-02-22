"""
===============
The Config Tree
===============

A configuration structure which supports cascading layers.

In ``vivarium`` it allows base configurations to be overridden by component
level configurations which are in turn overridden by model level configuration
which can be overridden by user supplied overrides. From the perspective
of normal client code the cascading is hidden and configuration values
are presented as attributes of the configuration object the values of
which are the value of that key in the outermost layer of configuration
where it appears.

For example:

.. code-block:: python

    >>> config = ConfigTree(layers=['inner_layer', 'middle_layer', 'outer_layer', 'user_overrides'])
    >>> config.update({'section_a': {'item1': 'value1', 'item2': 'value2'}, 'section_b': {'item1': 'value3'}}, layer='inner_layer')
    >>> config.update({'section_a': {'item1': 'value4'}, 'section_b': {'item1': 'value5'}}, layer='middle_layer')
    >>> config.update({'section_b': {'item1': 'value6'}}, layer='outer_layer')
    >>> config.section_a.item1
    'value4'
    >>> config.section_a.item2
    'value2'
    >>> config.section_b.item1
    'value6'

"""
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import yaml

from vivarium.exceptions import VivariumError


class ConfigurationError(VivariumError):
    """Base class for configuration errors."""

    def __init__(self, message: str, value_name: Optional[str]):
        self.value_name = value_name
        super().__init__(message)


class ConfigurationKeyError(ConfigurationError, KeyError):
    """Error raised when a configuration lookup fails."""

    pass


class ConfigTree:
    """A container for configuration information.

    Each configuration value is exposed as an attribute the value of which
    is determined by the outermost layer which has the key defined.

    """

    def __init__(
            self,
            data: Union[Dict, str, Path, "ConfigTree"] = None,
            layers: List[str] = None,
            name: str = "",
    ):
        """
        Parameters
        ----------
        data
            The :class:`ConfigTree` accepts many kinds of data:

             - :class:`dict` : Flat or nested dictionaries may be provided.
               Keys of dictionaries at all levels must be strings.
             - :class:`ConfigTree` : Another :class:`ConfigTree` can be
               used. All source information will be ignored and the source
               will be set to 'initial_data' and values will be stored at
               the lowest priority level.
             - :class:`str` : Strings provided can be yaml formatted strings,
               which will be parsed into a dictionary using standard yaml
               parsing. Alternatively, a path to a yaml file may be provided
               and the file will be read in and parsed.
             - :class:`pathlib.Path` : A path object to a yaml file will
               be interpreted the same as a string representation.

            All values will be set with 'initial_data' as the source and
            will use the lowest priority level. If values are set at higher
            priorities they will be used when the :class:`ConfigTree` is
            accessed.
        layers
            A list of layer names. The order in which layers defined
            determines their priority.  Later layers override the values from
            earlier ones.

        """
        self.__dict__["_layers"] = layers if layers else ["base"]
        self.__dict__["_children"] = {}
        self.__dict__["_frozen"] = False
        self.__dict__["_name"] = name
        self.update(data, layer=self._layers[0], source="initial data")

    def update(
            self,
            data: Union[Dict, str, Path, "ConfigTree", None],
            layer: str = None,
            source: str = None,
    ):
        """Adds additional data into the :class:`ConfigTree`.

        Parameters
        ----------
        data
            :func:`~ConfigTree.update` accepts many types of data.

             - :class:`dict` : Flat or nested dictionaries may be provided.
               Keys of dictionaries at all levels must be strings.
             - :class:`ConfigTree` : Another :class:`ConfigTree` can be
               used. All source information will be ignored and the
               provided layer and source will be used to set the metadata.
             - :class:`str` : Strings provided can be yaml formatted strings,
               which will be parsed into a dictionary using standard yaml
               parsing. Alternatively, a path to a yaml file may be provided
               and the file will be read in and parsed.
             - :class:`pathlib.Path` : A path object to a yaml file will
               be interpreted the same as a string representation.
        layer
            The name of the layer to store the value in.  If no layer is
            provided, the value will be set in the outermost (highest priority)
            layer.
        source
            The source to attribute the value to.

        Raises
        ------
        ConfigurationError
            If the :class:`ConfigTree` is frozen or attempting to assign
            an invalid value.
        ConfigurationKeyError
            If the provided layer does not exist.
        DuplicatedConfigurationError
            If a value has already been set at the provided layer or a value
            is already in the outermost layer and no layer has been provided.

        """
        if data is not None:
            data, source = self._coerce(data, source)
            for k, v in data.items():
                self._set_with_metadata(k, v, layer, source)

    def __setattr__(self, name, value):
        """Set a value on the outermost layer."""
        if name not in self:
            raise ConfigurationKeyError(
                "New configuration keys can only be created with the update method.",
                self._name,
            )
        self._set_with_metadata(name, value, layer=None, source=None)

    def __setitem__(self, name, value):
        """Set a value on the outermost layer."""
        if name not in self:
            raise ConfigurationKeyError(
                "New configuration keys can only be created with the update method.",
                self._name,
            )
        self._set_with_metadata(name, value, layer=None, source=None)

    def __getattr__(self, name):
        """Get a value from the outermost layer in which it appears."""
        return self.get_from_layer(name)

    def __getitem__(self, name):
        """Get a value from the outermost layer in which it appears."""
        return self.get_from_layer(name)

    def __delattr__(self, name):
        if name in self:
            del self._children[name]

    def __delitem__(self, name):
        if name in self:
            del self._children[name]

    def __contains__(self, name):
        """Test if a configuration key exists in any layer."""
        return name in self._children

    def __iter__(self):
        """Dictionary-like iteration."""
        return iter(self._children)

    def __len__(self):
        return len(self._children)

    def __dir__(self):
        return list(self._children.keys()) + dir(super(ConfigTree, self))

    def __repr__(self):
        return "\n".join(
            [
                "{}:\n    {}".format(name, repr(c).replace("\n", "\n    "))
                for name, c in self._children.items()
            ]
        )

    def __str__(self):
        return "\n".join(
            [
                "{}:\n    {}".format(name, str(c).replace("\n", "\n    "))
                for name, c in self._children.items()
            ]
        )
