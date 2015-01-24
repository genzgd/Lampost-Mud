from lampost.context.resource import m_requires
from lampost.gameops.action import ActionError
from lampost.lpmud.combat import consider_level

m_requires(__name__, 'log', 'dispatcher', 'tools')

chase_time = 120

class FightStats():
    def __init__(self, con_level):
        self.attack_results = {}
        self.defend_results = {}
        self.con_level = con_level
        self.last_exit = None
        self.last_seen = current_pulse()


class Fight():
    hunt_timer = None
    current_target = None

    def __init__(self, me):
        self.me = me
        self.opponents = {}

    def update_skills(self):
        self.attacks = [attack for attack in self.me.skills.values() if getattr(attack, 'msg_class', None) == 'attacked']
        self.attacks.sort(key=lambda x: x.points_per_pulse(self.me), reverse=True)
        self.defenses = [defense for defense in self.me.skills.values() if defense.template_id == 'defense' and not defense.auto_start]
        self.consider = self.me.considered()

    def add(self, opponent):
        try:
            self.opponents[opponent].last_seen = current_pulse()
        except KeyError:
            self.opponents[opponent] = FightStats(consider_level(self.consider, opponent.considered()))
            self.me.check_fight()

    def end(self, opponent, victory):
        try:
            del self.opponents[opponent]
            if opponent.last_opponent == self.me:
                opponent.last_opponent = None
        except KeyError:
            warn("Removing opponent not in fight")

    def end_all(self):
        for opponent in list(self.opponents.keys()):
            self.end(opponent, False)
            opponent.end_combat(self.me, True)
        self.clear_hunt_timer()

    def check_follow(self, opponent, ex):
        try:
            stats = self.opponents[opponent]
            stats.last_exit = ex
            stats.last_seen = current_pulse()
            self.select_action()
        except KeyError:
            pass

    def clear_hunt_timer(self):
        if self.hunt_timer:
            unregister(self.hunt_timer)
            del self.hunt_timer

    def select_action(self):
        self.clear_hunt_timer()
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
            self.me.start_action(attack, {'target': opponent, 'source': self.me, 'target_method': opponent.attacked})
            return
            # Try again when another skill because available
        if next_available < 10000:
            register_once(self.me.check_fight, next_available)

    def try_chase(self):
        stale_pulse = future_pulse(-chase_time)
        removed = [opponent for opponent, stats in self.opponents.items() if stats.last_seen < stale_pulse]
        for opponent in removed:
            self.end(opponent, False)
        if not self.opponents:
            return
        for stats in sorted(self.opponents.values(), key=lambda x: x.last_seen, reverse=True):
            if stats.con_level < 1 and stats.last_exit in self.me.env.action_providers:
                try:
                    self.me.start_action(stats.last_exit, {'source': self.me})
                    break
                except ActionError:
                    pass
        self.hunt_timer = register_p(self.select_action, seconds=10)
