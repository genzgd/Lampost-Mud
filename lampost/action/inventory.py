from lampost.dto.display import Display, DisplayLine
from lampost.mud.action import mud_action

@mud_action(('get', 'pick up'), 'get')
def get(source, target_method, **ignored):
    return target_method(source)

@mud_action(('drop', 'put down'), 'drop')
def drop(source, target_method, **ignored):
    return target_method(source)

@mud_action(('i', 'inven'))
def inven(source, **ignored):
    display = Display()
    if source.inven:
        for article in source.inven:
            display.append(DisplayLine(article.title))
    else:
        display.append(DisplayLine("You aren't carrying anything"))
    return display

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


