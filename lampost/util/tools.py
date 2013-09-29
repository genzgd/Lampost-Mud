from lampost.context.resource import provides
from lampost.comm.broadcast import substitute

@provides('tools', True)
class Tools(object):
    def combat_log(self, source, message, target=None):
        if hasattr(source, 'combat_log'):
            try:
                message = message.combat_log()
            except AttributeError:
                try:
                    message = message()
                except Exception as igor:
                    pass
            source.combat_log.display_line(substitute(message, source, target))
