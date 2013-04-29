from lampost.context.resource import m_requires, provides
from lampost.datastore.dbo import RootDBO
from lampost.gameops.action import make_action, ActionError

m_requires('log', 'datastore', 'dispatcher', __name__)

SKILL_TYPES = []


def skill_type(cls):
    def wrapper():
        SKILL_TYPES.append(cls)
        return cls
    return wrapper


@provides('skill_service')
class SkillService(object):

    def _post_init(self):
        register('baptise_player', self._baptise)
        self.skills = {skill_id: load_object(skill_type, skill_id) for skill_id in [fetch_set_keys(skill_type.dbo_set_key) for skill_type in SKILL_TYPES]}

    def _create_player(self):
        pass

    def _baptise(self, entity):
        for skill_id, skill_status in entity.skills.iteritems():
            try:
                skill = self.skills[skill_id]
                if skill.dbo_set_key == 'skill_attack':
                    player.enhance_soul(skill)
                if skill.dbo_set_key == 'skill_defense':
                    player.add_defense(skill)
            except KeyError:
                log.warn("No global skill {} found for player {}".format(skill_id, player.name))


@skill_type
class AttackSkill(RootDBO):
    dbo_fields = 'verb', 'desc', 'calc', 'effect', 'cost', 'cool_down', 'duration'
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













