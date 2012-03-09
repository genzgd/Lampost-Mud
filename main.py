'''
Created on Feb 15, 2012

@author: Geoff
'''
import sys

from lampost.mud import MudNature
from lampost.context import Context


if __name__ == "__main__":
    port = 2500
    db_num = 0
    db_host = "localhost"
    db_port = 6379
    try:
        for arg in sys.argv:
            name, value = arg.split(":")
            if name == "port":
                port = int(value)
            elif name == "db_host":
                db_host = value
            elif name == "db_port":
                db_port = int(value)
            elif name == "db_num":
                db_num = int(db_num)
    except Exception:
        print "Invalid argument: " + name
    else:                
        Context(MudNature(), port, db_host, db_port, db_num).start()