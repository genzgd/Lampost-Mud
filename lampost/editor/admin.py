import inspect

from lampost.client.handlers import MethodHandler
from lampost.context.resource import m_requires

m_requires(__name__, 'perm')

admin_ops = []


def admin_op(func):
    admin_ops.append({'op_name': func.__name__, 'args': inspect.getargspec(func)[0]})
    return func


class AdminHandler(MethodHandler):

    def operations(self):
        check_perm(self.player,  'supreme')
        self._return(admin_ops)

