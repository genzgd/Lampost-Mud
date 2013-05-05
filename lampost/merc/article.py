from lampost.merc.util import nudge
from lampost.model.article import ArticleTemplate
from lampost.mud.action import mud_action


class ArticleTemplateMerc(ArticleTemplate):
    new_fields = ("level", )
    template_fields = ArticleTemplate.template_fields + new_fields
    dbo_fields = ArticleTemplate.dbo_fields + new_fields
    level = 1

    def config_instance(self, instance):
        if instance.art_type == 'weapon':
            instance.damage_low = nudge(nudge(int(instance.level / 4 + 2)))
            instance.damage_high = nudge(nudge(int(3 * instance.level / 4 + 6)))
        elif instance.art_type == 'armor':
            defense = nudge(int(instance.level / 4 + 2))
            if instance.slot == 'torso':
                defense *= 3
            elif instance.slot in ['head', 'legs', 'cloak']:
                defense *= 2
            instance.defense = defense


@mud_action(('wear', 'equip', 'wield'), 'wear')
def wear(source, target, **ignored):
    source.equip_article(target)


@mud_action(('remove', 'unequip', 'unwield'), 'wear')
def remove(source, target, **ignored):
    source.remove_article(target)




