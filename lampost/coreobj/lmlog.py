'''
Created on Apr 18, 2012

@author: Geoff
'''
dispatcher = None

def db_log(log_msg):
    dispatcher.dispatch("db_log", log_msg)

def debug(debug_msg):
    dispatcher.dispatch("debug", debug_msg)