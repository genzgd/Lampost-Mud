import traceback

from sys import stderr
from datetime import datetime
from lampost.context.resource import m_requires, provides

m_requires('dispatcher', __name__)

def logged(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            stderr.write(str(datetime.now()) + " Unhandled exception\n")
            stderr.write(traceback.format_exc())
            dispatch("error", traceback.format_exc())
    return wrapper

@provides('log', True)
class Log(object):
    def db_log(self, log_msg):
        dispatch("db_log", log_msg)

    def debug(self, debug_msg):
        dispatch("debug", debug_msg)
    
    def error(self, error_msg):
        stderr.write(str(datetime.now()) + " " + (error_msg if error_msg else "") + "\n")
        stderr.write(traceback.format_exc())
        dispatch("error", error_msg)

