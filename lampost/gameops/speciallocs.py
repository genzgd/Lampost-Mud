'''
Created on Apr 15, 2012

@author: Geoff
'''
class Object(object):
    pass

creature_limbo = Object() 
creature_limbo.room_id = "creature_limbo"
creature_limbo.receive = lambda x: None
creature_limbo.get_children = lambda : []