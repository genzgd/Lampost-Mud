from collections import defaultdict
from random import randint

from tornado.ioloop import PeriodicCallback

from lampost.context.resource import provides, m_requires
from lampost.gameops.config import m_configured, configured


m_requires(__name__, 'log', 'datastore')



@provides('dispatcher', True)
@configured('maintenance_interval', 'pulse_interval')
class Dispatcher:
    def __init__(self):
        self._registrations = defaultdict(set)
        self._pulse_map = defaultdict(set)
        self._owner_map = defaultdict(set)

    def register(self, event_type, callback, owner=None, priority=0):
        return self._add_registration(Registration(event_type, callback, owner, priority))

    def unregister(self, registration):
        registration.cancel()
        owner_registrations = self._owner_map[registration.owner]
        owner_registrations.remove(registration)
        if not owner_registrations:
            del self._owner_map[registration.owner]
        event_registrations = self._registrations.get(registration.event_type)
        event_registrations.remove(registration)
        if not event_registrations:
            del self._registrations[registration.event_type]
        registration.owner = None
        registration.callback = None

    def unregister_type(self, owner, event_type):
        for registration in self._owner_map[owner].copy():
            if registration.event_type == event_type:
                self.unregister(registration)

    def register_p(self, callback, pulses=0, seconds=0, randomize=0, priority=0, repeat=True):
        if seconds:
            pulses = int(seconds * self.pulses_per_second)
            randomize = int(randomize * self.pulses_per_second)
        if randomize:
            randomize = randint(0, randomize)
        registration = PulseRegistration(pulses, callback, priority=priority, repeat=repeat)
        self._add_pulse(self._pulse_count + randomize, registration)
        return self._add_registration(registration)

    def register_once(self, *args, **kwargs):
        return self.register_p(repeat=False, *args, **kwargs)

    def current_pulse(self):
        return self._pulse_count

    def future_pulse(self, seconds):
        return int(self._pulse_count + self.pulses_per_second * seconds)

    def dispatch(self, event_type, *args, **kwargs):
        sorted_events = sorted(self._registrations.get(event_type, []), key=lambda reg: reg.priority)
        for registration in sorted_events:
            try:
                registration.callback(*args, **kwargs)
            except Exception:
                exception("Dispatch Error")

    def detach_events(self, owner):
        if owner in self._owner_map:
            for registration in self._owner_map[owner].copy():
                self.unregister(registration)

    def _pulse(self):
        self.dispatch('pulse')
        for reg in sorted(self._pulse_map[self._pulse_count], key=lambda reg: reg.priority):
            if reg.freq:
                try:
                    reg.callback()
                except Exception:
                    exception('Pulse Error')
                if reg.repeat:
                    self._add_pulse(self._pulse_count, reg)
        del self._pulse_map[self._pulse_count]
        self._pulse_count += 1

    def _add_registration(self, registration):
        self._registrations[registration.event_type].add(registration)
        self._owner_map[registration.owner].add(registration)
        return registration

    def _add_pulse(self, start, event):
        self._pulse_map[start + event.freq].add(event)

    def _post_init(self):
        self._pulse_count = load_raw('event_pulse', 0)
        self.register_p(lambda: save_raw('event_pulse', self._pulse_count), 100)

    def _on_configured(self):
        try:
            self.pulses_per_second = 1 / self.pulse_interval
            if hasattr(self, 'pulse_lc'):
                self.pulse_lc.stop()
            self.pulse_lc = PeriodicCallback(self._pulse, self.pulse_interval * 1000)
            self.pulse_lc.start()
            info("Pulse Event heartbeat started at {} seconds", self.pulse_interval)
        except KeyError:
            pass

        try:
            if hasattr(self, 'maintenance_lc'):
                self.maintenance_lc.stop()
            self.maintenance_lc = PeriodicCallback(lambda: self.dispatch('maintenance'), 60 * self.maintenance_interval * 1000)
            self.maintenance_lc.start()
            info("Maintenance Event heartbeat started at {} minutes", self.maintenance_interval)
        except KeyError:
            pass


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


def heartbeat_failed(failure):
    error(failure.getTraceback())
