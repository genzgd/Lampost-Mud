'''
Created on Feb 15, 2012

@author: Geoff
'''
from datetime import datetime
from json.decoder import JSONDecoder
from lampost.dto.display import Display, DisplayLine
from lampost.dto.link import LinkError, ERROR_SESSION_NOT_FOUND, \
    ERROR_NOT_LOGGED_IN
from lampost.dto.rootdto import RootDTO
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.web.static import File
from twisted.web.util import Redirect
import cgi
import traceback

FILE_WEB_CLIENT = "webclient"

URL_WEB_CLIENT = "webclient"
URL_LOGIN = "login"
URL_ACTION = "action"
URL_LINK = "link"
URL_DIALOG = "dialog"
URL_CONNECT = "connect"
URL_START = "/" + URL_WEB_CLIENT + "/start.html"

ARG_SESSION_ID = "session_id"
ARG_USER_ID = "user_id"
ARG_ACTION = "action"
ARG_DIALOG_RESPONSE = "response"


class LampostResource(Resource):
    IsLeaf = True
    def __init__(self, sm):
        Resource.__init__(self)
        Resource.decoder = JSONDecoder();
        self.putChild("", Redirect(URL_START))
        self.putChild(URL_WEB_CLIENT, File(FILE_WEB_CLIENT))
        self.putChild(URL_LOGIN, LoginResource(sm))
        self.putChild(URL_LINK, LinkResource(sm))
        self.putChild(URL_ACTION, ActionResource(sm))
        self.putChild(URL_CONNECT, ConnectResource(sm))
        self.putChild(URL_DIALOG, DialogResource(sm))
        self.putChild("ngclient", File("ngclient"));
        
        
class LoginResource(Resource):
    IsLeaf = True
    def __init__(self, sm):
        self.sm = sm
    
    def render_POST(self, request):
        content = self.decoder.decode(request.content.getvalue());
        session_id = content['session_id'];
        session = self.sm.get_session(session_id)
        if not session:
            return LinkError(ERROR_SESSION_NOT_FOUND).json
        user_id = content['user_id']
        return self.sm.login(session, user_id).json
    

class ConnectResource(Resource):
    IsLeaf = True
    def __init__(self, sm):
        self.sm = sm
        self.decoder = JSONDecoder()
    
    def render_POST(self, request):
        return self.sm.start_session().json
    
    
class LinkResource(Resource):
    IsLeaf = True   
    def __init__(self, sm):
        self.sm = sm
        self.decoder = JSONDecoder()
        
    def render_POST(self, request):
        content = self.decoder.decode(request.content.getvalue());
        user_session = self.sm.session_map.get(content['session_id'])
        if user_session:
            user_session.attach(request)
            return NOT_DONE_YET;
        return LinkError(ERROR_SESSION_NOT_FOUND).json


class DialogResource(Resource):
    IsLeaf = True
    def __init__(self, sm):
        self.sm = sm

    def render_POST(self, request):
        try:
            content = self.decoder.decode(request.content.getvalue());
            session_id = content['session_id'];
            session = self.sm.get_session(session_id)
            if not session:
                return  LinkError(ERROR_SESSION_NOT_FOUND).json
            feedback = session.dialog_response(content)
            if not feedback:
                return RootDTO(silent=True)
            if getattr(feedback, "json", None):
                return feedback.json
            else:
                return Display(feedback).json
        except:
            display = Display()
            display.append(DisplayLine(traceback.format_exc(), 0xff0000))
            return display.json
            
            
class ActionResource(Resource):
    IsLeaf = True
    def __init__(self, sm):
        self.sm = sm
    
    def render_POST(self, request):
        try:
            content = self.decoder.decode(request.content.getvalue());
            session_id = content['session_id'];
            session = self.sm.get_session(session_id)
            if not session:
                return LinkError(ERROR_SESSION_NOT_FOUND).json
            player = session.player  
            if not player:
                return LinkError(ERROR_NOT_LOGGED_IN).json
            
            action = cgi.escape(content['action']).strip()
            if not action:
                return;
            if action in ["quit", "logout", "log out"]:
                return self.sm.logout(session).json
            
            session.activity_time = datetime.now()
            feedback = player.parse(action)
            if not feedback:
                return Display("Nothing appears to happen.").json
            if getattr(feedback, "json", None):
                return feedback.json
            else:
                return Display(feedback).json
        except:
            display = Display()
            display.append(DisplayLine(traceback.format_exc(), 0xff0000))
            return display.json
            