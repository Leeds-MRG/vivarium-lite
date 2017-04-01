import pytest

from ceam.config_tree import ConfigTree

def test_single_layer():
    d = ConfigTree()
    d.test_key = 'test_value'
    d.test_key2 = 'test_value2'

    assert d.test_key == 'test_value'
    assert d.test_key2 == 'test_value2'

    d.test_key2 = 'test_value3'

    assert d.test_key2 == 'test_value3'
    assert d.test_key == 'test_value'

def test_get_missing():
    d = ConfigTree()
    d.test_key = 'test_value'

    # Missing keys should be empty containers
    assert len(d.missing_key) == 0

def test_multiple_layer_get():
    d = ConfigTree(layers=['first', 'second', 'third'])
    d.set_with_metadata('test_key', 'test_value', 'first')
    d.set_with_metadata('test_key', 'test_value2', 'second')
    d.set_with_metadata('test_key', 'test_value3', 'third')

    d.set_with_metadata('test_key2', 'test_value4', 'first')
    d.set_with_metadata('test_key2', 'test_value5', 'second')

    d.set_with_metadata('test_key3', 'test_value6', 'first')

    assert d.test_key == 'test_value3'
    assert d.test_key2 == 'test_value5'
    assert d.test_key3 == 'test_value6'

def test_outer_layer_set():
    d = ConfigTree(layers=['inner', 'outer'])
    d.set_with_metadata('test_key', 'test_value', 'inner')
    d.set_with_metadata('test_key', 'test_value2', 'outer')

    d.test_key = 'test_value3'

    assert d.test_key == 'test_value3'

def test_read_dict():
    d = ConfigTree(layers=['inner', 'outer'])
    d.read_dict({'test_key': 'test_value', 'test_key2': 'test_value2'}, layer='inner')
    d.read_dict({'test_key': 'test_value3'}, layer='outer')

    assert d.test_key == 'test_value3'
    assert d.test_key2 == 'test_value2'

def test_read_dict_nested():
    d = ConfigTree(layers=['inner', 'outer'])
    d.read_dict({'test_container': {'test_key': 'test_value', 'test_key2': 'test_value2'}}, layer='inner')
    d.read_dict({'test_container': {'test_key': 'test_value3'}}, layer='inner')

    assert d.test_container.test_key == 'test_value3'
    assert d.test_container.test_key2 == 'test_value2'

    d.read_dict({'test_container': {'test_key2': 'test_value4'}}, layer='outer')

    assert d.test_container.test_key2 == 'test_value4'

def test_source_metadata():
    d = ConfigTree(layers=['inner', 'outer'])
    d.read_dict({'test_key': 'test_value'}, layer='inner', source='initial_load')
    d.read_dict({'test_key': 'test_value2'}, layer='outer', source='update')

    assert d.source('test_key') == [('inner', 'initial_load', 'test_value'), ('outer', 'update', 'test_value2')]

def test_exception_on_source_for_missing_key():
    d = ConfigTree(layers=['inner', 'outer'])
    d.read_dict({'test_key': 'test_value'}, layer='inner', source='initial_load')

    with pytest.raises(KeyError) as excinfo:
        source = d.source('missing_key')
    assert 'missing_key' in str(excinfo.value)
