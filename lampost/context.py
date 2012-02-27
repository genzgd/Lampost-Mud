'''
Created on Feb 26, 2012

@author: Geoff
'''
from twisted.internet import reactor, task
from twisted.web.server import Site

from event import Dispatcher
from session import SessionManager
from server import LampostResource
from action import Action
from player import Player

class Context():
    def __init__(self, nature, port=2500):
        self.nature = nature;
        self.dispatcher = Dispatcher()
        Action.dispatcher = self.dispatcher
        Player.dispatcher = self.dispatcher
        self.sm = SessionManager(self.dispatcher, nature)
        self.site = Site(LampostResource(self.sm))
        self.port = port
        
        pulse = task.LoopingCall(self.dispatcher.pulse)
        pulse.start(nature.pulse_interval)
        
    def start(self):
        reactor.listenTCP(self.port, self.site) #@UndefinedVariable
        reactor.run() #@UndefinedVariable   