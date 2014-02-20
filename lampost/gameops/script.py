from lampost.context.resource import m_requires, inject
from lampost.datastore.dbo import RootDBO, DBOField
from lampost.gameops.action import item_action


m_requires('log', __name__)


class NameSpace(object):
    def script_items(self):
        return [(name, binding) for name, binding in self.exec_space.viewitems() if name not in self.original]

    def __call__(self):
        self.original = self.__dict__.copy()
        self.exec_space = self.__dict__.copy()
        return self.exec_space


def apply_script(host, script):
    script_code = compile(script.text, '<string>', 'exec')
    namespace = NameSpace()
    inject(namespace, 'log')
    inject(namespace, 'datastore')
    inject(namespace, 'dispatcher')
    namespace.item_action = item_action
    exec script_code in namespace()
    for name, binding in namespace.script_items():
        if name.startswith("__"):
            continue
        if hasattr(binding, '__call__'):
            bound_method = binding.__get__(host)
            setattr(host, name, bound_method)
            if hasattr(binding, 'verbs'):
                host.self_providers.append(bound_method)
        else:
            setattr(host, name, binding)


class Scriptable(object):

    scripts = DBOField([], 'script')

    def on_loaded(self):
        for script in self.scripts:
            if script.approved:
                apply_script(self, script)
        self.post_scripts()

    def post_scripts(self):
        pass


class Script(RootDBO):
    dbo_key_type = 'script'
    approved = DBOField(False)
    text = DBOField('')

    @property
    def dbo_set_key(self):
        return "area_scripts:{}".format(self.area_id)

    @property
    def area_id(self):
        return self.dbo_id.split(":")[0]





