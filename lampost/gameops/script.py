import bisect
from collections import defaultdict
import hashlib
import inspect

from lampost.context.resource import m_requires
from lampost.datastore.auto import AutoField
from lampost.datastore.dbo import CoreDBO
from lampost.datastore.dbofield import DBOField
from lampost.datastore.meta import CommonMeta


m_requires(__name__, 'log', 'datastore')


approved_hashes = ()
script_cache = {}


def _post_init():
    global approved_hashes
    approved_hashes = fetch_set_keys('approved_scripts')


def create_chain(funcs):

    def chained(self, *args, **kwargs):
        last_return = None
        for func in funcs:
            last_return = func(self, *args, last_return=last_return, **kwargs)
        return last_return
    return chained


def compile_script(text, name):
    try:
        return compile(text, '{}_shadow'.format(name), 'exec'), None
    except SyntaxError as err:
        err_str = "Syntax Error: {}  text:{}  line: {}  offset: {}".format(err.msg, err.text, err.lineno, err.offset)
    except BaseException as err:
        err_str = "Script Error: {}".format(err.msg)
    warn(err_str)
    return None, err_str


def approve_script(script):
    add_set_key('approved_scripts', script.hash)
    script_cache[script.hash] = script.code


def validate_script(script):
    try:
        return script_cache[script.hash]
    except KeyError:
        pass
    if script.hash not in approved_hashes:
        try:
            script_owner = script.dbo_owner.dbo_id
        except:
            script_owner = "Unknown"
        warn("Unapproved script {} from {} with hash {} rejected", script.name, script_owner, script_cache)
        return False

    code, _ = compile_script(script)
    if code:
        script_cache[script.hash] = code
    return code


class Shadow():
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
            exec(shadow.code, self.func.__globals__, shadow_locals)
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


class ShadowScript(CoreDBO):
    class_id = 'shadow_script'

    priority = DBOField(0)
    text = DBOField('', required=True)
    name = DBOField('', required=True)
    hash = DBOField('')
    code = None

    def __cmp__(self, other):
        if self.priority < other.priority:
            return -1
        if self.priority > other.priority:
            return 1
        return 0

    def on_loaded(self):
        self.code, err_str = validate_code(self.text, self.name)
        if err_str:
            warn("Script {} failed in {} ", self.name, self.dbo_owner.dbo_id)


class Scriptable(metaclass=CommonMeta):
    scripts = DBOField([], 'script')
    script_vars = DBOField({})
    shadows = DBOField([], 'shadow_script')
    shadow_chains = AutoField({})

    def on_loaded(self):
        chains = defaultdict(list)
        for shadow_script in self.shadows:
            if shadow_script.code:
                func_shadows = chains[shadow.name]
                bisect.insort(func_shadows, shadow)
        self.shadow_chains = chains
        self.load_scripts()

    @Shadow
    def load_scripts(self):
        pass



