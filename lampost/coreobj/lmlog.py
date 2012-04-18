'''
Created on Apr 18, 2012

@author: Geoff
'''
dispatcher = None

def debug(debug_msg):
    dispatcher.dispatch("debug", debug_msg)