import itertools

from lampost.datastore.dbo import DBOField
from lampost.env.feature import Feature
from lampost.gameops.action import item_actions
from lampost.model.item import Readable


inscription = Readable()
inscription.title = "Archaic Inscription"
inscription.text = "Herewith wilt thou be bound"
inscription.on_loaded()


@item_actions('touch')
class TouchStone(Feature):
    title = DBOField('Touchstone')
    desc = DBOField("An unadorned marble obelisk about five feet high.  There is an inscription in an archaic script on one side.")
    aliases = DBOField(["obelisk"])
    inscription = DBOField(inscription, Readable)

    def _action_providers(self):
        return [self.inscription]

    @property
    def target_providers(self):
        return [self.inscription]

    def rec_touch(self, source, **ignored):
        source.display_line("You feel a shock coursing through you.  It lasts a few seconds")
        source.bind_stone = room.dbo_id
