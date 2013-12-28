from lampost.mud.action import mud_action


@mud_action(('get', 'pick up'), 'get')
def get(source, target_method, **ignored):
    return target_method(source)


@mud_action(('drop', 'put down'), 'drop')
def drop(source, target_method, **ignored):
    return target_method(source)


@mud_action(('i', 'inven'))
def inven(source, **ignored):
    if source.inven:
        for article in source.inven:
            source.display_line(article.short_desc(source))
    else:
        source.display_line("You aren't carrying anything.")


class InvenContainer:
    def __init__(self):
        self.contents = []
        self.supports_drop = True

    def rec_entity_enters(self, source):
        self.contents.append(source)

    def rec_entity_leaves(self, source):
        self.contents.remove(source)

    def add(self, article):
        self.contents.append(article)


