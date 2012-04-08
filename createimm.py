'''
Created on Mar 4, 2012

@author: Geoffrey
'''
import sys

from lampost.datastore.dbconn import RedisStore
from lampost.player import Player
from lampost.immortal import IMM_LEVELS
from lampost.event import Dispatcher

if __name__ != "__main__":
    print "Invalid usage"
    sys.exit(2)

imm_name = None
db_pw = None
db_num = 0
db_host = "localhost"
db_port = 6379
try:
    for arg in sys.argv[1:]:
        name, value = arg.split(":")
        if name == "imm_name":
            imm_name = value
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
if not imm_name:
    print "imm_name:[Name] argument required"
    sys.exit(2)
    
redis = RedisStore(Dispatcher(), db_host, db_port, db_num, db_pw)
player = Player(imm_name)
player.imm_level = IMM_LEVELS["supreme"]
player.room_id = "immortal_citadel:cube"
if not redis.hydrate_object(player):
     redis.save_object(player)
 
     