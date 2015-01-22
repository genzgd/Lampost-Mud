from collections import defaultdict
from random import randint

from tornado.ioloop import PeriodicCallback

from lampost.context.resource import m_requires
from lampost.context.config import m_configured


m_requires(__name__, 'log', 'datastore')

_registrations = defaultdict(set)
_pulse_map = defaultdict(set)
_owner_map = defaultdict(set)
_pulse_count = 0

pulses_per_second = 0
pulse_lc = None
maintenance_lc = None


def register(event_type, callback, owner=None, priority=0):
    return _add_registration(Registration(event_type, callback, owner, priority))


def unregister(registration):
    registration.cancel()
    owner_registrations = _owner_map[registration.owner]
    owner_registrations.remove(registration)
    if not owner_registrations:
        del _owner_map[registration.owner]
    event_registrations = _registrations.get(registration.event_type)
    event_registrations.remove(registration)
    if not event_registrations:
        del _registrations[registration.event_type]
    registration.owner = None
    registration.callback = None


def unregister_type(owner, event_type):
    for registration in _owner_map[owner].copy():
        if registration.event_type == event_type:
            unregister(registration)


def register_p(callback, pulses=0, seconds=0, randomize=0, priority=0, repeat=True):
    if seconds:
        pulses = int(seconds * pulses_per_second)
        randomize = int(randomize * pulses_per_second)
    if randomize:
        randomize = randint(0, randomize)
    registration = PulseRegistration(pulses, callback, priority=priority, repeat=repeat)
    _add_pulse(_pulse_count + randomize, registration)
    return _add_registration(registration)


def register_once(*args, **kwargs):
    return register_p(repeat=False, *args, **kwargs)


def current_pulse():
    return _pulse_count


def future_pulse(seconds):
    return int(_pulse_count + pulses_per_second * seconds)


def dispatch(event_type, *args, **kwargs):
    sorted_events = sorted(_registrations.get(event_type, []), key=lambda reg: reg.priority)
    for registration in sorted_events:
        try:
            registration.callback(*args, **kwargs)
        except Exception:
            exception("Dispatch Error")


def detach_events(owner):
    if owner in _owner_map:
        for registration in _owner_map[owner].copy():
            unregister(registration)


def _pulse():
    global _pulse_count
    dispatch('pulse')
    for reg in sorted(_pulse_map[_pulse_count], key=lambda reg: reg.priority):
        if reg.freq:
            try:
                reg.callback()
            except Exception:
                exception('Pulse Error')
            if reg.repeat:
                _add_pulse(_pulse_count, reg)
    del _pulse_map[_pulse_count]
    _pulse_count += 1


def _add_registration(registration):
    _registrations[registration.event_type].add(registration)
    _owner_map[registration.owner].add(registration)
    return registration


def _add_pulse(start, event):
    _pulse_map[start + event.freq].add(event)


def _post_init():
    global _pulse_count
    _pulse_count = load_raw('event_pulse', 0)
    register_p(lambda: save_raw('event_pulse', _pulse_count), 100)


def _on_configured():
    global pulses_per_second, pulse_lc, maintenance_lc
    pulses_per_second = 1 / pulse_interval
    if pulse_lc:
        pulse_lc.stop()
    pulse_lc = PeriodicCallback(_pulse, pulse_interval * 1000)
    pulse_lc.start()
    info("Pulse Event heartbeat started at {} seconds", pulse_interval)

    if maintenance_lc:
        maintenance_lc.stop()
    maintenance_lc = PeriodicCallback(lambda: dispatch('maintenance'), 60 * maintenance_interval * 1000)
    maintenance_lc.start()
    info("Maintenance Event heartbeat started at {} minutes", maintenance_interval)


class Registration():
    def __init__(self, event_type, callback, owner=None, priority=0):
        self.event_type = event_type
        self.callback = callback
        self.owner = owner if owner else getattr(callback, '__self__', self)
        self.priority = priority

    def cancel(self):
        pass


class PulseRegistration(Registration):
    def __init__(self, freq, callback, owner=None, priority=0, repeat=True):
        super().__init__('pulse_i', callback, owner, priority)
        self.freq = freq
        self.repeat = repeat

    def cancel(self):
        self.freq = 0


m_configured(__name__, 'pulse_interval', 'maintenance_interval')
