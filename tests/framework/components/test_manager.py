import os

import pytest

from vivarium.framework.configuration import build_simulation_configuration
from vivarium.framework.components.manager import (ComponentManager, ComponentConfigError, ComponentList,
                                                   setup_components, apply_component_default_configuration)

from .mocks import MockComponentA, MockComponentB, NamelessComponent


@pytest.fixture
def apply_default_config_mock(mocker):
    return mocker.patch('vivarium.framework.components.manager.apply_component_default_configuration')


def test_apply_component_default_configuration():

    class UnladenSwallow:

        configuration_defaults = {
            'unladen_swallow': {
                'airspeed_velocity': 11,
            }
        }

    us = UnladenSwallow()
    config = build_simulation_configuration()
    assert 'unladen_swallow' not in config
    apply_component_default_configuration(config, us)
    assert config.unladen_swallow.metadata('airspeed_velocity') == [
        {'layer': 'component_configs', 'value': 11,
         'source': os.path.realpath(__file__), 'default': False}
    ]

    us = UnladenSwallow()
    us.__module__ = '__main__'
    config = build_simulation_configuration()
    assert 'unladen_swallow' not in config
    apply_component_default_configuration(config, us)
    assert config.unladen_swallow.metadata('airspeed_velocity') == [
        {'layer': 'component_configs', 'value': 11, 'source': '__main__', 'default': False}
    ]


def test_setup_components(mocker, apply_default_config_mock):
    config = build_simulation_configuration()
    builder = mocker.Mock()

    components = ComponentList([None, MockComponentA('Eric'),  MockComponentB('half', 'a', 'bee')])

    with pytest.raises(ComponentConfigError, match='None in component list'):
        setup_components(builder, components, config)

    components = ComponentList([MockComponentA('Eric'), MockComponentB('half', 'a', 'bee')])
    finished = setup_components(builder, components, config)
    mock_a, mock_b = finished

    apply_default_config_mock.assert_not_called()

    assert mock_a.builder_used_for_setup is None  # class has no setup method
    assert mock_b.builder_used_for_setup is builder
    assert mock_b.args == ('half', 'a', 'bee')

    class TestBee:
        configuration_defaults = {
            'test_bee': {
                'name': 'wasp',
                'location': 'next to my bed',
            }
        }

    test_bee = TestBee()
    components = ComponentList([MockComponentA('Eric'), MockComponentB('half', 'a', 'bee'), test_bee])
    apply_default_config_mock.reset_mock()
    setup_components(builder, components, config)

    apply_default_config_mock.assert_called_once()


@pytest.mark.parametrize("components", (
        (MockComponentA('Eric'), MockComponentB('half', 'a', 'bee')),
        (MockComponentA('Eric'),)
))
def test_ComponentManager__add_components(components):
    manager = ComponentManager()

    for list_type in ['_managers', '_components']:
        manager._add_components(getattr(manager, list_type), components)
        assert getattr(manager, list_type) == list(components)


@pytest.mark.parametrize("components", (
        (MockComponentA(), MockComponentA()),
        (MockComponentA(), MockComponentA(), MockComponentB('foo', 'bar')),
))
def test_ComponentManager__add_components_duplicated(components):
    manager = ComponentManager()

    for list_type in ['_managers', '_components']:
        with pytest.raises(ComponentConfigError, match='duplicate name'):
            manager._add_components(getattr(manager, list_type), components)


@pytest.mark.parametrize("components", (
        (None,),
        (NamelessComponent(),),
        (NamelessComponent(), MockComponentA())
))
def test_ComponentManager__add_components_unnamed(components):
    manager = ComponentManager()

    for list_type in ['_managers', '_components']:
        with pytest.raises(ComponentConfigError, match='no name'):
            manager._add_components(getattr(manager, list_type), components)


def test_ComponentManager__setup_components(mocker):
    config = build_simulation_configuration()
    manager = ComponentManager()
    builder = mocker.Mock()
    builder.components = manager

    manager.add_components([None, MockComponentA('Eric'), MockComponentB('half', 'a', 'bee')])
    with pytest.raises(ComponentConfigError, match='no name'):
        manager.setup_components(builder, config)

    manager._components = []
    manager.add_components([MockComponentA('Eric'), MockComponentB('half', 'a', 'bee')])
    manager.setup_components(builder, config)

    mock_a, mock_b, mock_b_child1, mock_b_child2, mock_b_child3 = manager._components

    assert mock_a.builder_used_for_setup is None  # class has no setup method
    assert mock_b.builder_used_for_setup is builder
    assert mock_b_child1.args == ('half',)
    assert mock_b_child1.builder_used_for_setup is builder
    assert mock_b_child2.args == ('a',)
    assert mock_b_child2.builder_used_for_setup is builder
    assert mock_b_child3.args == ('bee',)
    assert mock_b_child3.builder_used_for_setup is builder


class DummyMachine:
    configuration_defaults = {
        'factory': {
            'location': 'Building A'
        },
        'dummy_machine': {
            'id': 1,
        }
    }

    def __init__(self):
        self.name = 'dummy_machine'


class DummyMechanic:
    configuration_defaults = {
        'work_level': {
            'capacity': 2,  #per day
            'success_rate': .96
        },
        'dummy_machine': {
            'id': 123,
        }
    }

    def __init__(self):
        self.name = 'dummy_mechanic'


def test_default_configuration_set_by_one_component(mocker):

    machine = DummyMachine()
    mechanic = DummyMechanic()

    manager = ComponentManager()
    builder = mocker.Mock()
    builder.components = manager
    config = build_simulation_configuration()

    for key in ['factory', 'dummy_machine', 'work_level']:
        assert key not in config

    manager.add_components([machine, mechanic])

    with pytest.raises(ComponentConfigError):
        manager.setup_components(builder, config)


def test_default_configuration_set_by_one_component_as_0(mocker):

    DummyMachine.configuration_defaults['dummy_machine']['id'] = 0
    machine = DummyMachine()
    mechanic = DummyMechanic()

    manager = ComponentManager()
    builder = mocker.Mock()
    builder.components = manager
    config = build_simulation_configuration()

    manager.add_components([machine, mechanic])

    with pytest.raises(ComponentConfigError):
        manager.setup_components(builder, config)

    # case with empty string as default config value
    DummyMachine.configuration_defaults['dummy_machine']['id'] = ''
    machine = DummyMachine()
    manager = ComponentManager()
    builder = mocker.Mock()
    builder.components = manager
    config = build_simulation_configuration()
    manager.add_components([machine, mechanic])

    with pytest.raises(ComponentConfigError):
        manager.setup_components(builder, config)


def test_default_configuration_set_by_one_component_different_tree_depths(mocker):

    DummyMachine.configuration_defaults['dummy_machine']['id'] = {'number': 1, 'type': 'machine'}
    machine = DummyMachine()
    mechanic = DummyMechanic()

    manager = ComponentManager()
    builder = mocker.Mock()
    builder.components = manager
    config = build_simulation_configuration()

    manager.add_components([machine, mechanic])

    with pytest.raises(ComponentConfigError):
        manager.setup_components(builder, config)


def test_Component_List():
    component_list = ComponentList()

    component_0 = MockComponentA(name='component_0')
    component_list.append(component_0)

    component_1 = MockComponentA(name='component_1')
    component_list.insert(-1, component_1)

    # duplicates by name
    with pytest.raises(ComponentConfigError, match='duplicate name'):
        component_list.append(component_0)
    with pytest.raises(ComponentConfigError, match='duplicate name'):
        component_list.insert(-1, component_0)
    with pytest.raises(ComponentConfigError, match='duplicate name'):
        component_list[1] = component_0
    # no name
    with pytest.raises(ComponentConfigError, match='no name'):
        component_list.append(NamelessComponent())
    with pytest.raises(ComponentConfigError, match='no name'):
        component_list.insert(0, NamelessComponent())
    with pytest.raises(ComponentConfigError, match='no name'):
        component_list[0] = NamelessComponent()

    # __contains__
    assert component_0 in component_list
