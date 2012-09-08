from lampost.context.resource import provides

__author__ = 'Geoff'

@provides('perm')
class Permissions(object):
    levels = {'supreme':100000, 'admin':10000, 'creator':1000}

    def can_do(self, player, req_level):
        try:
            player_level = player.imm_level
        except AttributeError:
            try:
                player_level = player.player.imm_level
            except AttributeError:
                return False

        return player_level >= self.levels[req_level]

    def level(self, label):
        return self.levels.get(label, self.levels['admin'])

