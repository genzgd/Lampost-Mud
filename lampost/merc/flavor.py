from lampost.merc.article import ArticleTemplateMerc
from lampost.merc.combat import basic_hit
from lampost.merc.mobile import MobileTemplateMerc
from lampost.merc.player import PlayerMerc
from lampost.model.article import ArticleTemplate
from lampost.model.mobile import MobileTemplate
from lampost.model.player import Player
from lampost.mud.action import mud_action

from lampost.context.resource import m_requires

m_requires('cls_registry', 'context',  __name__)

equip_slots = ['none', 'finger', 'neck', 'torso', 'legs', 'head', 'feet', 'arms',
               'cloak', 'waist', 'wrist', 'one-hand', 'two-hand']

equip_types = ['armor', 'shield', 'weapon', 'treasure']


def _post_init():
    cls_registry.set_class(Player, PlayerMerc)
    cls_registry.set_class(ArticleTemplate, ArticleTemplateMerc)
    cls_registry.set_class(MobileTemplate, MobileTemplateMerc)

    context.set('equip_slots', equip_slots)
    context.set('equip_types', equip_types)


@mud_action(('kill', 'attack'), 'violence')
def kill(source, target, target_method, **ignored):
    if source == target:
        source.display_line("You cannot kill yourself.  This is a happy place.")
        return
    source.rec_violence(target)
    target_method(source)
    basic_hit(source, target)



