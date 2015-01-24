import inspect

from lampost.client.handlers import MethodHandler
from lampost.context.resource import m_requires

m_requires(__name__, 'perm')

admin_ops = {}


def admin_op(func):
    named_args = inspect.getargspec(func)[0]
    admin_ops[func.__name__] = {'func': func, 'dto': {'name': func.__name__, 'args': named_args, 'params': [None] * len(named_args)}}
    return func


class AdminHandler(MethodHandler):

    def operations(self):
        check_perm(self.player,  'supreme')
        return [op['dto'] for op in admin_ops.values()]

    def execute(self):
        exec_op = self.raw
        op = admin_ops[exec_op['name']]
        return op['func'](*exec_op['params'])

