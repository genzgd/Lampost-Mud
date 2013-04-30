from collections import defaultdict
from lampost.context.resource import m_requires, provides
from lampost.datastore.dbo import RootDBO
from lampost.gameops.action import make_action, ActionError

m_requires('log', 'datastore', 'dispatcher', __name__)

SKILL_TYPES = []


def skill_base(cls):
    def wrapper():
        SKILL_TYPES.append(cls)
        return cls
    return wrapper


class SkillCost(object):
    def __init__(self, pool=None, cost=None):
        self._costs = defaultdict(int)
        if pool:
            self.add(pool, cost)

    def add(self, pool, cost):
        self._costs[pool] += cost
        return self

    def apply(self, entity):
        for pool, cost in self._costs.iteritems():
            if getattr(entity, pool, 0) < cost:
                entity.start_refresh()
                raise ActionError("Your condition prevents you from doing that.")
        for pool, cost in self._costs.iteritems():
            setattr(entity, pool, getattr(entity, pool) - cost)
        entity.start_refresh()


@provides('skill_service')
class SkillService(object):

    def _post_init(self):
        register('player_baptise', self._baptise)
        self.skills = {}
        for skill_type in SKILL_TYPES:
            skills.update({skill_id: load_object(skill_type, skill_id) for skill_id in fetch_set_keys(skill_type.dbo_set_key)})

    def _create_player(self):
        pass

    def _baptise(self, entity):
        for skill_id, skill_status in entity.skills.iteritems():
            try:
                skill = self.skills[skill_id]
                if skill.dbo_set_key == 'skill_attack':
                    entity.enhance_soul(skill)
                if skill.dbo_set_key == 'skill_defense':
                    entity.add_defense(skill)
            except KeyError:
                log.warn("No global skill {} found for entity {}".format(skill_id, entity.name))


@skill_base
class AttackSkill(RootDBO):
    dbo_fields = 'verb', 'desc', 'calc', 'effect', 'costs', 'cool_down', 'duration'
    dbo_set_key = 'skill_attack'

    verb = None

    msg_class = "attack"
    desc = None
    effect = None
    cost = None
    cool_down = 0
    duration = 0

    def on_loaded(self):
        make_action(self.verb, self.msg_class)

    def __call__(self, source, target, **ignored):
        skill_status = source.skills[self.dbo_id]
        if skill_status.get('last_used', 0) + self.cool_down > dispatcher.pulse_count:
            raise ActionError("You cannot {} yet.".format(self.verb))
        self._check_costs(source)
        calc_results = self._calc_results(source, skill_status.get('level', 1))
        source.weapon_adjust()

        target_method(source, calc_results, duration)
        skill_status['last_used'] = dispatcher.pulse_count

    def _check_costs(self, source):
        pass

    def _calc_results(self, source, skill_level):
        magnitude = sum(getattr(source, calc['attr'], 0) * calc['factor'] for calc in self.calc) * skill_level
        return [{'attr': effect['attr'], 'value': magnitude * effect['factor']} for effect in self.effect]













