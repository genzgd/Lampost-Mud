import bisect
import inspect
from collections import defaultdict

from lampost.context.resource import m_requires
from lampost.core.auto import AutoField
from lampost.datastore.dbo import ChildDBO, DBOFacet
from lampost.datastore.dbofield import DBOField

m_requires(__name__, 'log', 'datastore', 'dispatcher')

script_cache = {}


def _post_init():
    register('maintenance', lambda: script_cache.clear())


def create_chain(funcs):

    def chained(self, *args, **kwargs):
        last_return = None
        for func in funcs:
            last_return = func(self, *args, last_return=last_return, **kwargs)
        return last_return
    return chained


def compile_script(script_hash, script_text, script_id):
    try:
        return script_cache[script_hash], None
    except KeyError:
        pass
    try:
        code = compile(script_text, '{}_shadow'.format(script_id), 'exec')
        script_cache[script_hash] = code
        return code, None
    except SyntaxError as err:
        err_str = "Syntax Error: {}  text:{}  line: {}  offset: {}".format(err.msg, err.text, err.lineno, err.offset)
    except BaseException as err:
        err_str = "Script Error: {}".format(err.msg)
    return None, err_str


class Shadow:
    def __init__(self, func):
        self.func = func
        self.name = func.__name__
        self.shadow_args = inspect.getargspec(func)

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        try:
            return instance.__dict__[self.name]
        except KeyError:
            pass
        return self.create_chain(instance)

    def create_chain(self, instance):
        shadow_funcs = []
        original_inserted = False
        for shadow in instance.shadow_chains.get(self.name, []):
            shadow_locals = {}
            exec(shadow.script.code, self.func.__globals__, shadow_locals)
            shadow_func = next(iter(shadow_locals.values()))
            if shadow.priority == 0:
                original_inserted = True
            elif shadow.priority > 0 and not original_inserted:
                shadow_funcs.append(self.func)
                original_inserted = True
            shadow_funcs.append(shadow_func)
        if not original_inserted:
            shadow_funcs.append(self.func)

        if len(shadow_funcs) == 1:
            bound_chain = shadow_funcs[0].__get__(instance)
        else:
            bound_chain = create_chain(shadow_funcs).__get__(instance)

        instance.__dict__[self.name] = bound_chain
        return bound_chain


class ShadowScript(ChildDBO):
    dbo_key_type = 'script'
    dbo_parent_type = 'area'

    title = DBOField('', required=True)
    cls_type = DBOField('any')
    cls_shadow = DBOField('any_func')
    text = DBOField('', required=True)
    script_hash = DBOField('')
    approved = DBOField(False)

    code = None

    def on_loaded(self):
        if self.approved:
            self.code, _ = compile_script(self.script_hash, self.text, self.dbo_id)
        else:
            info("Loading unapproved script {}", self.dbo_id)


class ShadowRef(ChildDBO):
    class_id = 'shadow_ref'
    name = DBOField('', required=True)
    priority = DBOField(0)
    script = DBOField(dbo_class_id='shadow_script', required=True)

    def __cmp__(self, other):
        if self.priority < other.priority:
            return -1
        if self.priority > other.priority:
            return 1
        return 0


class Scriptable(DBOFacet):
    shadow_refs = DBOField([], 'shadow_ref')
    script_vars = DBOField({})
    shadow_chains = AutoField({})

    def on_loaded(self):
        chains = defaultdict(list)
        for shadow_ref in self.shadow_refs:
            if shadow_ref.script.code:
                func_shadows = chains[shadow_ref.name]
                bisect.insort(func_shadows, shadow_ref)
        self.shadow_chains = chains
        self.load_scripts()

    @Shadow
    def load_scripts(self):
        pass
