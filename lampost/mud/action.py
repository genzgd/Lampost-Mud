from lampost.action.action import make_action

mud_actions = []
imm_actions = []

def mud_action(verbs, msg_class=None):
    def dec_wrapper(func):
        mud_actions.append(func)
        return make_action(func, verbs, msg_class)
    return dec_wrapper

def imm_action(verbs, msg_class=None, imm_level='creator'):
    def dec_wrapper(func):
        imm_actions.append(func)
        func.imm_level = imm_level
        return make_action(func, verbs, msg_class)
    return dec_wrapper


@mud_action('help')
def help(self, source, args, **ignored):
    action_set = source.actions.get(args)
    if not action_set:
        return "No matching command found"
    if len(action_set) > 1:
        return "Multiple matching commands"
    action = iter(action_set).next()
    return getattr(action, "help_text", "No help available.")
