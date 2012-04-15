'''
Created on Feb 17, 2012

@author: Geoff
'''
from random import randint
MAX_PULSE_QUEUE = 100;
PULSE_TIME = .25;

class PulseKey():
    def __init__(self, freq, next_loc):
        self.freq = freq
        self.next_loc = next_loc
        
    def __hash__(self):
        return self.freq * 101 + self.next_loc
        
    def __eq__(self, other):
        return type(self) == type(other) and self.freq == other.freq\
        and self.next_loc == other.next_loc
        
class PulseEvent():
    def __init__(self, freq, pulse_key):
        self.freq = freq
        self.pulse_key = pulse_key
                     
class Dispatcher:
    def __init__(self):
        self.registrations = {}
        self.pulse_queue = []
        for unused in range(MAX_PULSE_QUEUE): 
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
        event_type = registration.event_type
        event_registrations = self.registrations.get(event_type)
        if (event_registrations):
            event_registrations.remove(registration)
            if not event_registrations:
                del self.registrations[event_type]
                try:
                    pulse_key = event_type.pulse_key
                except AttributeError:
                    return
                del self.pulse_events[pulse_key]
                self.pulse_queue[pulse_key.next_loc].remove(event_type)              
        else:
            self.dispatch("debug", "Attempt to unregister {0} with registration".format(str(event_type)))
                    
        
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
            self.dispatch(event)
            next_loc = (self.pulse_loc + event.freq) % MAX_PULSE_QUEUE
            del self.pulse_events[event.pulse_key]
            event.pulse_key = PulseKey(event.freq, next_loc)
            self.pulse_events[event.pulse_key] = event
            self.pulse_queue[next_loc].add(event)
            
        events.clear()
        self.pulse_loc = self.pulse_loc + 1;
        if self.pulse_loc == MAX_PULSE_QUEUE:
            self.pulse_loc = 0;
                
    def register_p(self, freq, callback, randomize=0):
        if randomize:
            randomize = randint(0, randomize)
        next_loc = (self.pulse_loc + freq + randomize) % MAX_PULSE_QUEUE;
        pulse_key = PulseKey(freq, next_loc)
        pulse_event = self.pulse_events.get(pulse_key)
        if not pulse_event:
            pulse_event = PulseEvent(freq, pulse_key)
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
        