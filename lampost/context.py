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
    instance = None
     
    def __init__(self, nature, port=2500, db_host="localhost", db_port=6379, db_num=0, db_pw=None):
        self.nature = nature;
        self.dispatcher = Dispatcher()
        Action.dispatcher = self.dispatcher
        Entity.dispatcher = self.dispatcher
        self.datastore = RedisStore(self.dispatcher, db_host, db_port, db_num, db_pw)
        Action.datastore = self.datastore
        Entity.datastore = self.datastore
        self.sm = SessionManager(self.dispatcher, self.datastore, nature)
      
        self.site = Site(LampostResource(self.sm))
        self.port = port
        self.nature.create(self.datastore)
        Context.instance = self
        
        pulse = task.LoopingCall(self.dispatcher.pulse)
        pulse.start(nature.pulse_interval)
        
    def start(self):
        reactor.listenTCP(self.port, self.site) #@UndefinedVariable
        reactor.run() #@UndefinedVariable