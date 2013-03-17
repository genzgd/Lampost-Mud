from collections import defaultdict
from random import randint
from twisted.internet import task

from lampost.context.resource import provides, m_requires
from lampost.util.lmlog import logged

m_requires("log", __name__)


@provides('dispatcher', True)
class Dispatcher:
    def __init__(self, max_pulse_queue=1000, pulse_interval=.25):
        self._registrations = defaultdict(set)
        self._pulse_map = defaultdict(set)
        self._owner_map = defaultdict(set)
        self.pulse_count = 0
        self.max_pulse_queue = max_pulse_queue
        self.pulse_interval = pulse_interval
        self.pulses_per_second = 1 / pulse_interval

    def register(self, event_type, callback):
        return self._add_registration(Registration(event_type, callback))

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

    def register_p(self, callback, pulses=0, seconds=0, randomize=0):
        if seconds:
            pulses = int(seconds * self.pulses_per_second)
            randomize = int(randomize * self.pulses_per_second)
        if pulses >= self.max_pulse_queue:
            raise ValueError("Pulse Frequency Greater Than Pulse Queue Size")
        if randomize:
            randomize = randint(0, randomize)
        registration = PulseRegistration(pulses, callback)
        self._add_pulse(self.pulse_count + randomize, registration)
        return self._add_registration(registration)

    def dispatch(self, event_type, *args, **kwargs):
        for registration in self._registrations.get(event_type, set()).copy():
            registration.callback(*args, **kwargs)

    def detach_events(self, owner):
        for registration in self._owner_map[owner].copy():
            self.unregister(registration)

    @logged
    def _pulse(self):
        self.dispatch('pulse')
        map_loc = self.pulse_count % self.max_pulse_queue
        for event in self._pulse_map[map_loc]:
            if event.freq:
                event.callback()
                self._add_pulse(self.pulse_count, event)
        del self._pulse_map[map_loc]
        self.pulse_count += 1

    def _add_registration(self, registration):
        self._registrations[registration.event_type].add(registration)
        self._owner_map[registration.owner].add(registration)
        return registration

    def _add_pulse(self, start, event):
        next_loc = (start + event.freq) % self.max_pulse_queue
        self._pulse_map[next_loc].add(event)

    @logged
    def _post_init(self):
        task.LoopingCall(self._pulse).start(self.pulse_interval)
        info("Event heartbeat started", self)


class Registration(object):
    def __init__(self, event_type, callback):
        self.event_type = event_type
        self.callback = callback
        self.owner = getattr(callback, 'im_self', self)

    def cancel(self):
        pass


class PulseRegistration(Registration):
    def __init__(self, freq, callback):
        super(PulseRegistration, self).__init__('pulse_i', callback)
        self.freq = freq

    def cancel(self):
        self.freq = 0

