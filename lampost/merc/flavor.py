import lampost.player.player
import lampost.model.article
import lampost.mobile.mobile

import lampost.merc.player
import lampost.merc.article
import lampost.merc.mobile

from lampost.merc.combat import basic_hit
from lampost.mud.action import mud_action

from lampost.context.resource import m_requires

m_requires('cls_registry', __name__)

cls_registry.set_class(lampost.player.player.Player, lampost.merc.player.PlayerMerc)
cls_registry.set_class(lampost.model.article.ArticleTemplate, lampost.merc.article.ArticleTemplateMerc)
cls_registry.set_class(lampost.mobile.mobile.MobileTemplate, lampost.merc.mobile.MobileTemplateMerc)

@mud_action(('kill', 'attack'), 'violence')
def kill(source, target, target_method, **ignored):
    source.rec_violence(target)
    target_method(source)
    return basic_hit(source, target)



