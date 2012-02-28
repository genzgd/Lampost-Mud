'''
Created on Feb 12, 2012

@author: Geoff
'''
from datetime import datetime, timedelta

from dto.display import Display, DisplayLine
from dto.link import LinkCancel, LinkGood
from dto.rootdto import RootDTO
from player import Player
from event import PulseEvent

LINK_DEAD_INTERVAL = timedelta(seconds=5)
LINK_DEAD_PRUNE = timedelta(minutes=2)
LINK_IDLE_REFRESH = timedelta(seconds=45)


class SessionManager():
    def __init__(self, dispatcher, nature):
        self.dispatcher = dispatcher
        self.nature = nature;
        self.next_session_id = 0
        self.session_map = {}
        self.player_list_dto = RootDTO()
        self.dispatcher.register("refresh_link_status", self.refresh_link_status)
        self.dispatcher.dispatch_p(PulseEvent("refresh_link_status", 20, repeat=True))                      
 
    def get_next_id(self):
        self.next_session_id = self.next_session_id + 1 
        return str(self.next_session_id)
    
    def get_session(self, session_id):
        return self.session_map.get(session_id)   
        
    def start_session(self):
        session_id = self.get_next_id()
        session = UserSession(self.dispatcher)
        self.session_map[session_id] = session
        return RootDTO(connect=session_id).merge(self.player_list_dto)
                    
    def display_players(self):
        for session in self.session_map.itervalues():
            session.append(self.player_list_dto)

    def refresh_link_status(self, *args):
        player_list = {};
        now = datetime.now()
        for session_id, session in self.session_map.items():
            if session.ld_time:
                if now - session.ld_time > LINK_DEAD_PRUNE:
                    del self.session_map[session_id]
                    continue
            elif session.request:
                if now - session.attach_time > LINK_IDLE_REFRESH:
                    session.append(RootDTO(keepalive=True))
            elif now - session.attach_time > LINK_DEAD_INTERVAL:
                session.link_failed("Timeout")
            if session.player:
                player_list[session.player.name] = session.player_status()
        self.player_list_dto = RootDTO(player_list=player_list)
        self.display_players()
                 
    def login(self, session_id, user_id):
        session = self.session_map.get(session_id)
        player = Player(user_id, session)
        session.player = player
        self.nature.baptise(player)
        session.display_line(DisplayLine("Welcome " + player.name,  0x002288))
        #self.player_list_dto.
        return RootDTO(login="good")
    
        
class UserSession():
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.output = RootDTO()
        self.player = None;  
        self.activity_time = datetime.now()
        self.attach_time = datetime.now()
        self.ld_time = None
        self.request = None
        self.pulse_reg = None
        
    def player_status(self):
        if self.ld_time:
            return "Link Dead"
        return "Active"
    
    def attach(self, request):
        if self.request:
            self.push(LinkCancel())
        self.attach_time = datetime.now()
        self.ld_time = None
        self.request = request
        self.request.notifyFinish().addErrback(self.link_failed)
    
    def link_failed(self, error):
        self.ld_time = datetime.now()
        self.request = None
    
    def append(self, data):
        if not self.pulse_reg:
            self.pulse_reg = self.dispatcher.register("pulse", self.push_output)
        self.output.merge(data)
         
    def display_line(self, display_line):
        display = Display()
        display.append(display_line)
        self.append(display)
        
    def push_output(self):
        if self.request:
            self.push(self.output.merge(LinkGood()))
            self.output = RootDTO()
            self.pulse_reg.detach()
            self.pulse_reg = None
            
    def push(self, output):
        self.request.write(self.output.json)
        self.request.finish()
        self.request = None