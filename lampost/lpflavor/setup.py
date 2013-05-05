from lampost.context.resource import m_requires
from lampost.lpflavor.combat import AttackSkill
from lampost.lpflavor.skill import DEFAULT_SKILLS
from lampost.model.race import PlayerRace

m_requires('datastore', __name__)


def first_time_setup():
    unknown_race = PlayerRace('unknown')
    unknown_race.name = "Unknown"
    save_object(unknown_race)
    default_skills()


def default_skills():
    punch_skill = AttackSkill('punch')
    punch_skill.desc = "The basic, time honored punch."
    punch_skill.costs = {'action': 10, 'stamina': 10}
    punch_skill.duration = 10
    punch_skill.damage_type = "blunt"
    punch_skill.weapon_type = "unarmed"
    punch_skill.damage_calc = {'str': 2}
    punch_skill.accuracy_calc = {'agi': 5}
    create_object(punch_skill)

