from lampost.context.resource import m_requires, register
from lampost.gameops.action import make_action, convert_verbs

m_requires(__name__, 'log')
_mud_actions = {}

register('mud_actions', _mud_actions)
imm_actions = set()


def mud_action(verbs, msg_class=None, **kwargs):
    def dec_wrapper(func):
        action = make_action(func, msg_class=msg_class, **kwargs)
        for verb in convert_verbs(verbs):
            if verb in _mud_actions:
                error("Adding mud action for existing verb {}", verb)
            else:
                _mud_actions[verb] = action
    return dec_wrapper


def imm_action(verbs, msg_class=None, imm_level='builder', **kwargs):
    def dec_wrapper(func):
        imm_actions.add(func)
        func.imm_level = imm_level
        return make_action(func, verbs, msg_class, **kwargs)
    return dec_wrapper
