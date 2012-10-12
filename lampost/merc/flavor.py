import lampost.player.player
import lampost.model.article
import lampost.mobile.mobile

import lampost.merc.player
import lampost.merc.article
import lampost.merc.mobile

from lampost.merc.combat import basic_hit
from lampost.mud.action import mud_action

from lampost.context.resource import m_requires

m_requires('cls_registry', 'context',  __name__)

equip_slots = ['none', 'finger', 'neck', 'torso', 'legs', 'head', 'feet', 'arms',
               'cloak', 'waist', 'wrist', 'one-hand', 'two-hand']

equip_types = ['armor', 'shield', 'weapon', 'treasure']


def init():
    cls_registry.set_class(lampost.player.player.Player, lampost.merc.player.PlayerMerc)
    cls_registry.set_class(lampost.model.article.ArticleTemplate, lampost.merc.article.ArticleTemplateMerc)
    cls_registry.set_class(lampost.mobile.mobile.MobileTemplate, lampost.merc.mobile.MobileTemplateMerc)

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



