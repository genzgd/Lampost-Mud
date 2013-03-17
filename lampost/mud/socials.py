from lampost.comm.broadcast import BroadcastMap
from lampost.context.resource import provides, requires
from lampost.datastore.dbo import RootDBO


@provides('social_registry')
@requires('datastore', 'mud_actions')
class SocialRegistry(object):

    def __init__(self):
        self._socials = {}

    def emote(self, source, target, verb, **ignored):
        source.broadcast(broadcast_map=self._socials[verb[0]], target=target)

    def load_socials(self):
        self.mud_actions.add_verb(('socials',), self.socials)
        self.emote.__func__.msg_class = 'rec_social'
        for social_key in self.datastore.fetch_set_keys("socials"):
            social_id = social_key.split(":")[1]
            social = self.datastore.load_object(Social, social_id)
            self.insert(social)

    def insert(self, social):
        self._socials[social.dbo_id] = BroadcastMap(**social.map)
        self.mud_actions.add_verb((social.dbo_id,), self.emote)

    def delete(self, social_verb):
        del self._socials[social_verb]
        self.mud_actions.rem_verb((social_verb,), self.emote)

    def socials(self, **ignored):
        return " ".join(sorted(self._socials.keys()))

    def get(self, social_id):
        return self._socials.get(social_id)


class Social(RootDBO):
    dbo_set_key = 'socials'
    dbo_key_type = 'social'
    dbo_fields = 'map',

    def __init__(self, social_id):
        self.dbo_id = social_id
        self.map = {}



