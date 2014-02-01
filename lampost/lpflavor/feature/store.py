from lampost.datastore.dbo import DBOField
from lampost.env.feature import Feature
from lampost.gameops.action import item_action, ActionError
from lampost.model.article import Article
from lampost.mud.inventory import InvenContainer


class Store(Feature):
    currency = DBOField()
    inven = DBOField(InvenContainer(), InvenContainer)
    title = DBOField('Vending Machine')
    desc = DBOField("A rickety vending machine.  It looks like you can both buy and sell pretty much anything here.")

    @item_action(target_class="inven", msg_class="drop")
    def rec_sell(self, source, target, quantity=None, **ignored):
        if quantity or target.quantity:
            raise ActionError("You can't sell that kind of item.")
        source.check_drop(target, None)
        source.remove_inven(target)
        self.inven.append(target)
        self.room.dirty = True
        source.broadcast(s="You sell {N}.", e="{n} sell {N}.", target=target)

    @item_action(msg_class="get")
    def rec_buy(self, source, target, **ignored):
        if target not in self.inven:
            raise ActionError("That is not in the store.")
        if not self.currency:
            self.dispense(target, source)

    def rec_examine(self, source, **ignored):
        super(Store, self).rec_examine(source)
        if self.inven:
            source.display_line("It currently contains:")
            for article in self.inven:
                article.rec_glance(source)
        else:
            source.display_line("Unfortunately, it's out of everything.")

    def dispense(self, target, source):
        self.inven.remove(target)
        target.enter_env(source)
        source.broadcast(s="You buy {N}.",e="{n} buys {N}.", target=target)
        self.room.dirty = True

    def on_created(self):
        self.target_providers = self.inven.contents
