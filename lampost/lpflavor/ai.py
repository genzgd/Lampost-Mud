from lampost.context.resource import m_requires
from lampost.gameops.action import ActionError

m_requires('log', 'dispatcher', __name__)


class FightStats():
    def __init__(self):
        self.attack_results = {}
        self.defend_results = {}


class Fight():
    def __init__(self, me):
        self.me = me
        self.opponents = {}
        self.update_skills()

    def update_skills(self):
        self.attacks = [attack for attack in self.me.skills.viewvalues() if getattr(attack, 'msg_class', None) == 'rec_attack']
        self.attacks.sort(key=lambda x: x.points_per_pulse(self.me), reverse=True)
        self.defenses = [defense for defense in self.me.skills.viewvalues() if defense.skill_type == 'defense' and not skill.auto_start]

    def add(self, opponent):
        if opponent not in self.opponents.viewkeys():
            self.opponents[opponent] = FightStats()

    def end(self, opponent, victory):
        try:
            del self.opponents[opponent]
        except KeyError:
            warn("Removing opponent not in fight")

    def lose(self):
        for opponent in self.opponents.viewkeys():
            opponent.end_combat(self.me, True)
        self.opponents.clear()

    def select_action(self):
        try:
            # Select opponent with the current lowest health
            opponent = reduce(lambda opp1, opp2: opp1 if opp1.health < opp2 else opp2, self.opponents.keys())
        except TypeError:
            return 0
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
            self.me.start_action(attack, {'target': opponent, 'source': self.me, 'target_method': opponent.rec_attack})
            return 0
        # Try again when another skill because available
        if next_available < 10000:
            register_p(self.me.check_fight, pulses=next_available, repeat=False)
