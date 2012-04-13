'''
Created on Feb 17, 2012

@author: Geoff
'''
MAX_PULSE_QUEUE = 100;
PULSE_TIME = .25;

class PulseKey():
    def __init__(self, freq, queue_start):
        self.freq = freq
        self.queue_start = queue_start
        
    def __hash__(self):
        return self.freq * 101 + self.queue_start
        
    def __eq__(self, other):
        return type(self) == type(other) and self.freq == other.freq\
        and self.queue_start == other.queue_start
        
class PulseEvent():
    def __init__(self, freq):
        self.event_type = self
        self.freq = freq
        self.repeat = True
             

class Dispatcher:
    def __init__(self):
        self.registrations = {}
        self.pulse_queue = [];
        for i in range(0, MAX_PULSE_QUEUE): #@UnusedVariable
            self.pulse_queue.append(set())
        self.pulse_events = {}
        self.pulse_loc = 0;
      
    def register(self, event_type, callback):
        registration = Registration(event_type, callback, self)
        event_registrations = self.registrations.get(event_type)
        if not event_registrations:
            event_registrations = set()
            self.registrations[event_type] = event_registrations
        event_registrations.add(registration)
        return registration                               
        
    def unregister(self, registration):
        event_registrations = self.registrations[registration.event_type]
        if (event_registrations):
            event_registrations.remove(registration)
            if not event_registrations:
                del self.registrations[registration.event_type]    
        
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
        events = self.pulse_queue[self.pulse_loc]
        for event in events:
            self.dispatch(event.event_type)
            if event.repeat:
                next_loc = (self.pulse_loc + event.freq) % MAX_PULSE_QUEUE
                next_events = self.pulse_queue[next_loc]
                next_events.add(event)
        events.clear()
        self.pulse_loc = self.pulse_loc + 1;
        if self.pulse_loc == MAX_PULSE_QUEUE:
            self.pulse_loc = 0;
                
    def register_p(self, freq, callback):
        next_loc = (self.pulse_loc + freq) % MAX_PULSE_QUEUE;
        pulse_key = PulseKey(freq, next_loc)
        pulse_event = self.pulse_events.get(pulse_key)
        if not pulse_event:
            pulse_event = PulseEvent(freq)
            self.pulse_events[pulse_key] = pulse_event
            self.pulse_queue[next_loc].add(pulse_event)
        return self.register(pulse_event, callback)

            
class Registration():
    def __init__(self, event_type, callback, dispatcher):
        self.event_type = event_type
        self.callback = callback
        self.dispatcher = dispatcher
        
    def detach(self):
        self.dispatcher.unregister(self)
        