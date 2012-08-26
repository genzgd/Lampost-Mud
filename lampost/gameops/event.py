import sys
from random import randint
from lampost.context.resource import provides, requires, inject
 
MAX_PULSE_QUEUE = 100
PULSE_TIME = .25
PULSES_PER_SECOND = int(1 / PULSE_TIME)

inject(sys.modules[__name__], 'log')

@provides('dispatcher')
@requires('log')
class Dispatcher:
    def __init__(self):
        self.registrations = {}
        self.pulse_map = {}
        self.pulse_count = 0
      
    def register(self, event_type, callback):
        registration = Registration(event_type, callback)
        self._add_registration(registration)
        return registration
        
    def unregister(self, registration):
        registration.cancel()
        event_type = registration.event_type
        event_registrations = self.registrations.get(event_type)
        if event_registrations:
            try:
                event_registrations.remove(registration)
            except KeyError:
                error("No registration found for " + str(event_type))
            if not event_registrations:
                del self.registrations[event_type]
        else:
            self.dispatch("debug", "Attempt to unregister {0} with registration".format(str(event_type)))

    def register_p(self, freq, callback, randomize=0):
        if randomize:
            randomize = randint(0, randomize)
        registration = PulseRegistration(freq, callback)
        self._add_registration(registration)
        self._add_pulse(self.pulse_count + randomize, registration)
        return registration

    def dispatch(self, event_type, data=None):
        event_registrations = self.registrations.get(event_type)
        if event_registrations:
            for registration in event_registrations.copy():
                if data:
                    registration.callback(data)
                else:
                    registration.callback()
           
    def pulse(self):
        self.dispatch("pulse")
        events = self.pulse_map.get(self.pulse_count % MAX_PULSE_QUEUE, set())
        for event in events:
            if not event.freq:
                continue
            try:
                event.callback()
            except:
                error("Error processing event " + str(event))
            self._add_pulse(self.pulse_count, event)
        events.clear()
        self.pulse_count += 1

    def _add_registration(self, registration):
        event_registrations = self.registrations.get(registration.event_type)
        if not event_registrations:
            event_registrations = set()
            self.registrations[registration.event_type] = event_registrations
        event_registrations.add(registration)

    def _add_pulse(self, start, event):
        next_loc = (start + event.freq) % MAX_PULSE_QUEUE
        event_set = self.pulse_map.get(next_loc)
        if not event_set:
            event_set = set()
            self.pulse_map[next_loc] = event_set
        event_set.add(event)

@requires('dispatcher')
class Registration():
    def __init__(self, event_type, callback):
        self.event_type = event_type
        self.callback = callback

    def detach(self):
        self.unregister(self)

    def cancel(self):
        pass

class PulseRegistration(Registration):
    def __init__(self, freq, callback):
        self.event_type = "pulse_i"
        self.callback = callback
        self.freq = freq

    def cancel(self):
        self.freq = 0

        