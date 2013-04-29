DAMAGE_TYPES = {'blunt': {'desc': 'Blunt trauma (clubs, maces)'},
                'pierce': {'desc': 'Piercing damage (spears, arrows)'},
                'slash': {'desc' : 'Slash damage (swords, knives)'},
                'cold': {'desc': 'Cold'},
                'fire': {'desc': 'Fire'},
                'shock': {'desc': 'Electric'},
                'acid': {'desc': 'Acid'},
                'poison': {'desc': 'Poison'},
                'psych': {'desc': 'Mental/psychic damage'},
                'spirit': {'desc': 'Spiritual damage'}}


class Attack(object):
    def __init__(self, accuracy, damage, speed):
        self.accuracy = accuracy
        self.damage = damage
        self.speed = speed


def process_attack(source, target, attack):
    damage_results = process_damage(source, target, attack.accuracy, attack.damage)


def process_damage(source, target, accuracy, damage):
    for damage in attack.damage:
        accuracy = attack.accuracy - target.dodge(source, damage.damage_type)
        if accuracy <= 0:
            result = 'dodge'
        parry = attack.accuracy - target.parry(source, damage.damage_type)
        if parry <= 0:
            result = 'parry'
            continue







