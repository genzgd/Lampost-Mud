from collections import defaultdict
from lampost.context.resource import m_requires, provides
from lampost.datastore.dbo import RootDBO
from lampost.gameops.action import make_action, ActionError

m_requires('log', 'datastore', 'dispatcher', __name__)

SKILL_TYPES = []
DEFAULT_SKILLS = ['punch']


def base_skill():
    def wrapper(cls):
        SKILL_TYPES.append(cls)
        return cls
    return wrapper


class SkillStatus(RootDBO):
    dbo_fields = 'skill_level', 'last_used'
    last_used = 0
    skill_level = 1


class SkillEffect(RootDBO):
    dbo_fields = 'attr', 'pool', 'amount', 'expiration'
    attr = None
    pool = None
    amount = 0
    expiration = 0


@provides('skill_service')
class SkillService(object):

    def _post_init(self):
        register('player_create', self._player_create)
        register('player_baptise', self._baptise)
        self.skills = {}
        for skill_type in SKILL_TYPES:
            self.skills.update({skill_id: load_object(skill_type, skill_id) for skill_id in fetch_set_keys(skill_type.dbo_set_key)})

    def _player_create(self, player):
        player.skills = {}
        for skill_id in DEFAULT_SKILLS:
            player.skills[skill_id] = SkillStatus()

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


class SkillCost(object):
    def __init__(self, pool=None, cost=None):
        self.costs = defaultdict(int)
        if pool:
            self.add(pool, cost)

    def add(self, pool, cost):
        self.costs[pool] += cost
        return self

    def apply(self, entity):
        for pool, cost in self.costs.iteritems():
            if getattr(entity, pool, 0) < cost:
                entity.start_refresh()
                raise ActionError("Your condition prevents you from doing that.")
        for pool, cost in self.costs.iteritems():
            setattr(entity, pool, getattr(entity, pool) - cost)
        entity.start_refresh()


class BaseSkill():
    dbo_fields = 'verb', 'desc', 'costs',  'pre_reqs', 'prep_time', 'cool_down', 'prep_map', 'success_map', 'fail_map'
    verb = None
    desc = None
    prep_time = 0
    cool_down = 0
    pre_reqs = []
    skill_cost = SkillCost()
    prep_map = {}
    success_map = {}
    fail_map = {}
    display = 'default'

    def on_loaded(self):
        if not self.verb:
            self.verb = self.dbo_id
        make_action(self, self.verb, self.msg_class)

    @property
    def costs(self):
        return self.skill_cost.costs

    @costs.setter
    def costs(self, value):
        self.skill_cost = SkillCost()
        for pool, cost in value.iteritems():
            self.skill_cost.add(pool, cost)

    def prepare_action(self, source, target, **kwargs):
        skill_status = source.skills[self.dbo_id]
        if skill_status.last_used + self.cool_down > dispatcher.pulse_count:
            raise ActionError("You cannot {} yet.".format(self.verb))
        if self.prep_map:
            source.broadcast(display=self.display, target=target, **self.prep_map)

    def __call__(self, source, **kwargs):
        self.skill_cost.apply(source)
        skill_status = source.skills[self.dbo_id]
        self.invoke(skill_status, source, **kwargs)
        skill_status.last_used = dispatcher.pulse_count












