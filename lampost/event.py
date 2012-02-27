'''
Created on Feb 17, 2012

@author: Geoff
'''
MAX_PULSE_QUEUE = 50;
PULSE_TIME = .25;

class Dispatcher:
    def __init__(self):
        self.registrations = {}
        self.pulse_queue = [];
        for i in range(0, MAX_PULSE_QUEUE): #@UnusedVariable
            self.pulse_queue.append(set())
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
            self.dispatch(event.event_type, event.data)
            if event.repeat:
                next_loc = (self.pulse_loc + event.pulse) % MAX_PULSE_QUEUE
                next_events = self.pulse_queue[next_loc]
                next_events.add(event)
        events.clear()
        self.pulse_loc = self.pulse_loc + 1;
        if self.pulse_loc == MAX_PULSE_QUEUE:
            self.pulse_loc = 0;
                
    def dispatch_p(self, pulse_event):
        event_loc = (self.pulse_loc + pulse_event.pulse) % MAX_PULSE_QUEUE;
        self.pulse_queue[event_loc].add(pulse_event)
    

class PulseEvent():
    def __init__(self, event_type, pulse, data=None, repeat=False):
        self.event_type = event_type
        self.data = data
        self.pulse = pulse
        self.repeat = repeat          

            
class Registration():
    def __init__(self, event_type, callback, dispatcher):
        self.event_type = event_type
        self.callback = callback
        self.dispatcher = dispatcher
        
    def detach(self):
        self.dispatcher.unregister(self)
        