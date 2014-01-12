from lampost.context.resource import m_requires

m_requires('log', __name__)

class FightStats():
    def __init__(self):
        self.attack_results = {}
        self.defend_results = {}


class Fight():
    def __init__(self, me):
        self.me = me
        self.opponents = {}

    def add(self, opponent):
        if opponent not in self.opponents:
            self.opponents[opponent] = FightStats()

    def remove(self, opponent):
        try:
            del self.opponents[opponent]
        except KeyError:
            warn("Removing opponent not in fight")

    def lose(self):
        self.opponents.clear()

    def select_action(self):
        if not self.opponents:
            return
        attacks = [attack for attack in self.me.skills.viewvalues() if getattr(attack, 'msg_class', None) == 'rec_attack' and attack.available]
        attacks.sort(key=lambda x: x.points_per_pulse(self.me), reverse=True)
        opponent = reduce(lambda opp1, opp2: opp1 if opp1.health < opp2 else opp2, self.opponents.keys())
        if attacks:
            self.me.start_action(attacks[0], {'target': opponent, 'source': self.me, 'target_method': opponent.rec_attack})
