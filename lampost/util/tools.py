from lampost.context.resource import provides
from lampost.comm.broadcast import substitute

@provides('tools', True)
class Tools(object):
    def combat_log(self, source, message, target=None):
        if getattr(source, 'combat_log', None):
            source.combat_log.display_line(substitute(message, source, target))
