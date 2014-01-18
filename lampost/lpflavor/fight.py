from lampost.context.resource import m_requires
from lampost.gameops.action import ActionError
from lampost.gameops.parser import has_action
from lampost.lpflavor.combat import consider_level

m_requires('log', 'dispatcher', 'tools', __name__)


class FightStats():
    def __init__(self, con_level):
        self.attack_results = {}
        self.defend_results = {}
        self.con_level = con_level


class Fight():
    hunt_timer = None
    current_target = None

    def __init__(self, me):
        self.me = me
        self.opponents = {}

    def update_skills(self):
        self.attacks = [attack for attack in self.me.skills.viewvalues() if getattr(attack, 'msg_class', None) == 'rec_attack']
        self.attacks.sort(key=lambda x: x.points_per_pulse(self.me), reverse=True)
        self.defenses = [defense for defense in self.me.skills.viewvalues() if defense.skill_type == 'defense' and not skill.auto_start]
        self.consider = self.me.rec_consider()

    def add(self, opponent):
        if opponent not in self.opponents.viewkeys():
            self.opponents[opponent] = FightStats(consider_level(self.consider, opponent.rec_consider()))

    def end(self, opponent, victory):
        try:
            del self.opponents[opponent]
        except KeyError:
            warn("Removing opponent not in fight")

    def end_all(self):
        for opponent in self.opponents.viewkeys():
            opponent.end_combat(self.me, True)
        self.opponents.clear()
        self.clear_hunt_timer()

    def check_follow(self, opponent, ex):
        try:
            stats = self.opponents[opponent]
            stats.last_exit = ex
            # Don't follow if we have other local opponents
            if [opponent for opponent in self.opponents.keys() if opponent.env == self.me.env]:
                return
            self.try_chase()
        except KeyError:
            pass

    def clear_hunt_timer(self):
        if self.hunt_timer:
            unregister(self.hunt_timer)
            del self.hunt_timer

    def select_action(self):
        local_opponents = [opponent for opponent in self.opponents.keys() if opponent.env == self.me.env]
        if local_opponents:
            local_opponents.sort(key=lambda opponent: opponent.health)
            self.select_attack(local_opponents[0])
        else:
            self.try_chase()

    def select_attack(self, opponent):
        next_available = 100000
        for attack in self.attacks:
            available = attack.available
            if available > 0:
                next_available = min(available, next_available)
                continue
            try:
                self.me.check_costs(attack.costs)
                attack.validate(self.me, opponent)
            except ActionError:
                continue
            self.me.last_opponent = opponent
            self.me.start_action(attack, {'target': opponent, 'source': self.me, 'target_method': opponent.rec_attack})
            return
            # Try again when another skill because available
        if next_available < 10000:
            register_once(self.me.check_fight, next_available)

    def try_chase(self):
        opponent_escapes = [stats.last_exit for stats in self.opponents.viewvalues() if stats.con_level < 1 and stats.last_exit]
        if opponent_escapes:
            self.me.start_action(opponent_escapes[0], {'source': self.me})
        else:
            self.hunt_timer = register_once(self.end_all, seconds=120)
