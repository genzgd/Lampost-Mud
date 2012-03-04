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
from entity import Entity
from datastore.dbconn import RedisStore

class Context():
    def __init__(self, nature, port=2500):
        self.nature = nature;
        self.dispatcher = Dispatcher()
        Action.dispatcher = self.dispatcher
        Entity.dispatcher = self.dispatcher
        self.datastore = RedisStore(self.dispatcher)
        Action.datastore = self.datastore
        Entity.datastore = self.datastore
        self.sm = SessionManager(self.dispatcher, nature)
        self.site = Site(LampostResource(self.sm))
        self.port = port
        self.nature.create()
        
      
        pulse = task.LoopingCall(self.dispatcher.pulse)
        pulse.start(nature.pulse_interval)
        
    def start(self):
        reactor.listenTCP(self.port, self.site) #@UndefinedVariable
        reactor.run() #@UndefinedVariable   