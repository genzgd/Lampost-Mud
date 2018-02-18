import bisect

from lampost.di.resource import Injected, module_inject

ev = Injected('dispatcher')
module_inject(__name__)

_pulse_map = {}


def add_action(source, action, pulse, callback, priority=0):
    if not pulse:
        process_immediate(source, action, callback)
        return
    pulse_key = ev.current_pulse + pulse
    current_diff = pulse
    sys_action = SystemAction(source, action, priority, callback)

    try:
        pulse_actions = _pulse_map[pulse_key]
    except KeyError:
        _pulse_map[pulse_key] = pulse_actions = []
        ev.register_once(process_actions, current_diff, kwargs={'pulse_key': pulse_key})
    bisect.insort_right(pulse_actions, sys_action)


def process_actions(pulse_key):
    affected = set()
    actions = _pulse_map[pulse_key]
    for sys_action in actions:
        affected.add(sys_action.source)
        sys_action.callback(sys_action.action, affected)
    del _pulse_map[pulse_key]
    for entity in affected:
        try:
            entity.resolve_actions()
        except AttributeError:
            pass


def process_immediate(source, action, callback):
    affected = {source}
    callback(action, affected)
    for entity in affected:
        try:
            entity.resolve_actions()
        except AttributeError:
            pass


class SystemAction:
    def __init__(self, source, action, priority, callback):
        self.source = source
        self.action = action
        self.priority = priority
        self.callback = callback

    def __lt__(self, other):
        return self.priority < other.priority
