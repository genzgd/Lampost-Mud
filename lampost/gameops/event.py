from collections import defaultdict
from random import randint
from twisted.internet import task

from lampost.context.resource import provides, m_requires
from lampost.util.lmlog import logged

m_requires("log", "datastore", __name__)


@provides('dispatcher', True)
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

    def unregister_type(self, owner, event_type):
        for registration in self._owner_map[owner].copy():
            if registration.event_type == event_type:
                self.unregister(registration)

    def register_p(self, callback, pulses=0, seconds=0, randomize=0, priority=0):
        if seconds:
            pulses = int(seconds * self.pulses_per_second)
            randomize = int(randomize * self.pulses_per_second)
        if randomize:
            randomize = randint(0, randomize)
        registration = PulseRegistration(pulses, callback, priority=priority)
        self._add_pulse(self.pulse_count + randomize, registration)
        return self._add_registration(registration)

    def dispatch(self, event_type, *args, **kwargs):
        sorted_events = sorted(self._registrations.get(event_type, []), key=lambda reg: reg.priority)
        for registration in sorted_events:
            registration.callback(*args, **kwargs)

    def detach_events(self, owner):
        for registration in self._owner_map[owner].copy():
            self.unregister(registration)

    def _pulse(self):
        self.dispatch('pulse')
        for reg in sorted(self._pulse_map[self.pulse_count], key=lambda reg: reg.priority):
            if reg.freq:
                try:
                    reg.callback()
                except Exception as pulse_error:
                    error('Pulse Error', 'Dispatcher', pulse_error)
                self._add_pulse(self.pulse_count, reg)
        del self._pulse_map[self.pulse_count]
        self.pulse_count += 1

    def _add_registration(self, registration):
        self._registrations[registration.event_type].add(registration)
        self._owner_map[registration.owner].add(registration)
        return registration

    def _add_pulse(self, start, event):
        self._pulse_map[start + event.freq].add(event)

    def _post_init(self):
        try:
            self.pulse_count = load_raw('event_pulse')
        except TypeError:
            self.pulse_count = 0
            save_raw('event_pulse', self.pulse_count)
        self.register_p(lambda: save_raw('event_pulse', self.pulse_count), 100)
        self.register("server_settings", self._update_settings, priority=-1000)

    def _update_settings(self, server_settings):
        try:
            pulse_interval = server_settings['pulse_interval']
            self.pulses_per_second = 1 / pulse_interval
            if hasattr(self, 'pulse_lc'):
                self.pulse_lc.stop()
            self.pulse_lc = task.LoopingCall(self._pulse).start(pulse_interval, False)
            self.pulse_lc.addErrback(heartbeat_failed)
            info("Pulse Event heartbeat started at {} seconds".format(pulse_interval), self)
        except KeyError:
            pass

        try:
            maintenance_interval = server_settings['maintenance_interval']
            if hasattr(self, 'maintenance_lc'):
                self.maintenance_lc.stop()
            self.maintenance_lc = task.LoopingCall(lambda: self.dispatch('maintenance')).start(60 * maintenance_interval, False)
            self.maintenance_lc.addErrback(heartbeat_failed)
            info("Maintenance Event heartbeat started at {} minutes".format(maintenance_interval), self)
        except KeyError:
            pass


class Registration(object):
    def __init__(self, event_type, callback, owner=None, priority=0):
        self.event_type = event_type
        self.callback = callback
        self.owner = owner if owner else getattr(callback, 'im_self', self)
        self.priority = priority

    def cancel(self):
        pass


class PulseRegistration(Registration):
    def __init__(self, freq, callback, owner=None, priority=0):
        super(PulseRegistration, self).__init__('pulse_i', callback, owner, priority)
        self.freq = freq

    def cancel(self):
        self.freq = 0


def heartbeat_failed(failure):
    error(failure.getTraceback(), "Dispatcher")

