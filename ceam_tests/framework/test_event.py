import pytest

from datetime import datetime

import pandas as pd
import numpy as np

from ceam.framework.event import Event, EventManager

def test_split_event():
    index1 = pd.Index(range(10))
    index2 = pd.Index(range(5))
    current_time = datetime.now()

    e1 = Event(current_time, index1)
    e2 = e1.split(index2)

    assert e1.time == e2.time == current_time
    assert e1.index is index1
    assert e2.index is index2

def test_emission():
    signal = [False]
    def listener(*args, **kwargs):
        signal[0] = True

    manager = EventManager()
    emitter = manager.get_emitter('test_event')
    manager.register_listener('test_event', listener)
    emitter(Event(None, None))

    assert signal[0]

    signal[0] = False

    emitter = manager.get_emitter('test_unheard_event')
    emitter(Event(None, None))
    assert not signal[0]

def test_listener_priority():
    signal = [False, False, False]
    def listener1(*args, **kwargs):
        signal[0] = True
        assert not signal[1]
        assert not signal[2]
    def listener2(*args, **kwargs):
        signal[1] = True
        assert signal[0]
        assert not signal[2]
    def listener3(*args, **kwargs):
        signal[2] = True
        assert signal[0]
        assert signal[1]

    manager = EventManager()
    emitter = manager.get_emitter('test_event')
    manager.register_listener('test_event', listener1, priority=0)
    manager.register_listener('test_event', listener2)
    manager.register_listener('test_event', listener3, priority=9)

    emitter(Event(None, None))
    assert np.all(signal)
