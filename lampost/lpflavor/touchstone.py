from lampost.datastore.dbo import DBOField
from lampost.env.feature import Feature
from lampost.gameops.action import item_actions


@item_actions('touch')
class TouchStone(Feature):
    title = DBOField('Touchstone')
    desc = DBOField("An unadorned marble obelisk about five feet high.")
    aliases = DBOField(["obelisk"])

    def rec_touch(self, source, **ignored):
        source.display_line("You feel a shock coursing through you.  It lasts a few seconds")



