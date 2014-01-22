from lampost.context.resource import provides


@provides('tools', True)
class Tools(object):
    def combat_log(self, source, message, target=None):
        if hasattr(source.env, 'combat_log'):
            try:
                message = message.combat_log()
            except AttributeError:
                try:
                    message = message()
                except TypeError:
                    pass
            source.env.broadcast(s=message, source=source, target=target)
