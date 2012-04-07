'''
Created on Feb 15, 2012

@author: Geoff
'''
import sys

from lampost.mud import MudNature
from lampost.context import Context


if __name__ != "__main__":
    print "Invalid usage"
    sys.exit(2)
    
port = 2500
db_num = 0
db_host = "localhost"
db_port = 6379
db_pw = None
try:
    for arg in sys.argv[1:]:
        name, value = arg.split(":")
        if name == "port":
            port = int(value)
        elif name == "db_host":
            db_host = value
        elif name == "db_port":
            db_port = int(value)
        elif name == "db_num":
            db_num = int(db_num)
        elif name == "db_pw":
            db_pw = value
        else:
            print "Invalid argument: " + name
            sys.exit(2)
except ValueError:
    print "Invalid argument format: " + arg
    sys.exit(2)
Context(MudNature(), port, db_host, db_port, db_num, db_pw).start()