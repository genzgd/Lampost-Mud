import itertools

from lampost.datastore.dbo import DBOField
from lampost.env.feature import Feature
from lampost.gameops.action import item_action
from lampost.model.item import Readable


inscription = Readable()
inscription.title = "Archaic Inscription"
inscription.text = "Herewith wilt thou be bound"
inscription.on_loaded()


class Touchstone(Feature):
    title = DBOField('Touchstone')
    desc = DBOField("An unadorned marble obelisk about five feet high.  There is an inscription in an archaic script on one side.")
    aliases = DBOField(["obelisk"])
    inscription = DBOField(inscription, Readable)

    @item_action()
    def rec_touch(self, source, **ignored):
        source.display_line("You feel a shock coursing through you.  It lasts a few seconds")
        source.touchstone = self.room.dbo_id

    def on_created(self):
        self.target_providers.append(self.inscription)
        self.action_providers.append(self.inscription)
