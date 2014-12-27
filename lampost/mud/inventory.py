from lampost.datastore.dbofield import DBOField

from lampost.gameops.display import EXIT_DISPLAY
from lampost.model.item import BaseItem
from lampost.mud.action import mud_action


@mud_action(('get', 'pick up'), 'get', target_class="env_items", quantity=True)
def get(source, target_method, quantity=None,  **_):
    target_method(source, quantity)


@mud_action(('drop', 'put down'), 'drop', target_class="inven", quantity=True)
def drop(source, target_method, quantity=None, **_):
    return target_method(source, quantity)


@mud_action(('i', 'inven'))
def inven(source, **_):
    if source.inven:
        source.display_line("You are carrying:")
        for article in source.inven:
            source.display_line("&nbsp;&nbsp;{}".format(article.short_desc()), EXIT_DISPLAY)
    else:
        source.display_line("You aren't carrying anything.")


class InvenContainer(BaseItem):
    class_id = 'container'

    contents = DBOField([], 'untyped')

    def __iter__(self):
        for item in self.contents:
            yield item

    def __len__(self):
        return len(self.contents)

    def __contains__(self, item):
        return item in self.contents

    def __getitem__(self, key):
        return self.contents[key]

    def append(self, item):
        self.contents.append(item)

    def remove(self, item):
        self.contents.remove(item)



