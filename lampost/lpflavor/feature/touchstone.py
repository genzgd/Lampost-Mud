from lampost.datastore.dbo import DBOField
from lampost.env.feature import Feature
from lampost.gameops.action import obj_action
from lampost.model.item import Readable, BaseItem


class Inscription(BaseItem, Readable):
    class_id = 'inscription'

inscription = Inscription()
inscription.title = "Archaic Inscription"
inscription.text = "Herewith wilt thou be bound"
inscription.desc = "An inscription written in the flowery letters of a time long past."
inscription._on_loaded()


class Touchstone(Feature):
    sub_class_id = 'touchstone'

    title = DBOField('Touchstone')
    desc = DBOField("An unadorned marble obelisk about five feet high.  There is an inscription in an archaic script on one side.")
    aliases = DBOField(["obelisk"])
    inscription = DBOField(inscription, 'inscription')

    @obj_action(target_class="func_owner")
    def touch(self, source, **_):
        source.display_line("You feel a shock coursing through you.  It lasts a few seconds")
        source.touchstone = self.room.dbo_id

    def on_created(self):
        self.target_providers.append(self.inscription)
        self.instance_providers.append(self.inscription)
