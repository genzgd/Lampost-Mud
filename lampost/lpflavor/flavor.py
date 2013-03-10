from lampost.model.player import Player
from lampost.lpflavor.player import PlayerLP

from lampost.context.resource import m_requires

m_requires('cls_registry', 'context',  __name__)

equip_slots = ['none', 'finger', 'neck', 'torso', 'legs', 'head', 'feet', 'arms',
               'cloak', 'waist', 'wrist', 'one-hand', 'two-hand']

equip_types = ['armor', 'shield', 'weapon', 'treasure']


def init():
    cls_registry.set_class(Player, PlayerLP)


    context.set('equip_slots', equip_slots)
    context.set('equip_types', equip_types)





