import itertools
from collections import deque

from lampost.context.resource import m_requires
from lampost.core.auto import AutoField
from lampost.datastore.dbofield import DBOField
from lampost.gameops.action import obj_action, ActionError
from lampost.model.item import BaseItem

m_requires(__name__, 'dispatcher')


class Buyback():
    def __init__(self, owner, article, price, pulse):
        self.owner = owner
        self.article = article
        self.price = price
        self.pulse = pulse


def buyback_gen(target_key, entity, action):
    for buyback in action.__self__.buybacks:
        if buyback.owner == entity.dbo_id and target_key in buyback.article.target_keys:
            yield buyback
buyback_gen.abs_msg = "{target} is not available to buy back"


class Store(BaseItem):
    class_id = 'store'

    currency = DBOField(None, 'article')
    inven = DBOField([], 'untyped')
    perm_inven = DBOField([], 'article')
    title = DBOField('Vending Machine')
    desc = DBOField("A rickety vending machine.  It looks like you can both buy and sell pretty much anything here.")
    markup = DBOField(0)
    discount = DBOField(0)
    buybacks = AutoField(deque())
    buyback_reg = AutoField()
    buyback_seconds = DBOField(5 * 60)

    def _price(self, article):
        return (article.value // self.currency.value * (100 + self.markup)) // 100

    def _offer(self,article):
        return (article.value // self.currency.value * (100 - self.discount)) // 100

    @obj_action(target_class="inven", msg_class="drop")
    def sell(self, source, target, quantity=None, **_):
        if quantity or target.quantity:
            raise ActionError("You can't sell that kind of item.")
        if self.currency:
            if not target.value:
                raise ActionError("That's not worth anything.")
            offer = self.currency.create_instance()
            offer.quantity = self._offer(target)
            offer.enter_env(source)
            sell_msg = ''.join(("You sell {N} for ", offer.name, '.'))
            self.buybacks.appendleft(Buyback(source.dbo_id, target, offer.quantity, current_pulse()))
            self._start_buyback()
        else:
            sell_msg = "You deposit {N}."
            self.add_inven(target)

        source.check_drop(target, None)
        source.remove_inven(target)
        source.broadcast(s=sell_msg, e="{n} sells {N}.", target=target)

    @obj_action()
    def buy(self, source, target, **_):
        if self.currency and target.value:
            money = self._take_money(source, self._price(target))
            self_msg = ''.join(("You buy {N} for ", money.name, '.'))
        else:
            self_msg = "You withdraw {N}."
        if target in self.perm_items:
            target = target.template.create_instance()
        else:
            self.inven.remove(target)
            self.dbo_owner.dirty = True
        target.enter_env(source)
        source.broadcast(s=self_msg,e="{n} buys {N}.", target=target)

    @obj_action(verbs=("buy back",), target_class=buyback_gen)
    def buyback(self, source, target, **_):
        article = target.article
        money = self._take_money(source, target.price)
        self_msg = ''.join(("You recover {N} for ", money.name, '.'))
        self.buybacks.remove(target)
        article.enter_env(source)
        source.broadcast(s=self_msg, e="{n) recovers {N}", target=article)

    def examine(self, source, **_):
        super().examine(source)
        if self.perm_items or self.inven:
            source.display_line("It currently contains:")
            for article in self.target_providers:
                if self.currency:
                    price = self._price(article)
                    name = self.currency.plural_name(price)
                else:
                    price, name = '', ''
                source.display_line('{} {} {}'.format(article.short_desc(), price, name))
        else:
            source.display_line("Unfortunately, it's out of everything.")
        buybacks = [buyback for buyback in self.buybacks if buyback.owner == source.dbo_id]
        if buybacks:
            source.display_line("You can 'buy back' these items")
            for buyback in buybacks:
                source.display_line('{} {} {}'.format(buyback.article.short_desc(), buyback.price, self.currency.plural_name(buyback.price)))

    def _take_money(self, source, price):
        for inven in source.inven:
            if inven.template == self.currency:
                if inven.quantity < price:
                    raise ActionError("You only have {}.".format(inven.name))
                else:
                    return inven.take_from(source, price)
        raise ActionError("You don't have any {}!".format(self.currency.plural_title))

    def _start_buyback(self):
        self.pulse_stamp = current_pulse()
        if not self.buyback_reg:
            self.buyback_reg = register_p(self._trim_buybacks, seconds=30)

    def _trim_buybacks(self):
        stale_pulse = future_pulse(-self.buyback_seconds)
        try:
            last = self.buybacks[-1]
            while last.pulse < stale_pulse:
                self.add_inven(self.buybacks.pop().article)
                last = self.buybacks[-1]
            self.pulse_stamp = current_pulse()
        except IndexError:
            unregister(self.buyback_reg)
            self.buyback_reg = None

    def add_inven(self, article):
        for perm_article in self.perm_items:
            if article.template == perm_article.template and article.cmp_value == perm_article.cmp_value:
                return
        self.inven.append(article)
        self.dbo_owner.dirty = True

    def on_loaded(self):
        self.perm_items = [template.create_instance() for template in self.perm_inven]

    @property
    def target_providers(self):
        return itertools.chain(self.inven, self.perm_items)
