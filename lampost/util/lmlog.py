'''
Created on Apr 18, 2012

@author: Geoff
'''
import traceback

from sys import stderr
from datetime import datetime


dispatcher = None

def db_log(log_msg):
    dispatcher.dispatch("db_log", log_msg)

def debug(debug_msg):
    dispatcher.dispatch("debug", debug_msg)
    
def error(error_msg):
    stderr.write(str(datetime.now()) + " " + (error_msg if error_msg else ""))
    stderr.write(traceback.format_exc())
    dispatcher.dispatch("error", error_msg)