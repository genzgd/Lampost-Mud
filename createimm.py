'''
Created on Mar 4, 2012

@author: Geoffrey
'''
import sys

from lampost.datastore.dbconn import RedisStore
from lampost.player import Player
from lampost.immortal import IMM_LEVELS
from lampost.event import Dispatcher

if __name__ == "__main__":
     player_name = sys.argv[1]
     db_num = 0 if len(sys.argv) < 3 else int(sys.argv[2])
     redis = RedisStore(Dispatcher(), db_num)
     
     player = Player(player_name)
     player.imm_level = IMM_LEVELS["supreme"]
     if not redis.load_object(player):
         redis.save_object(player)
     
     