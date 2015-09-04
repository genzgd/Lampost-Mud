import bisect
import inspect
import hashlib

from collections import defaultdict

from lampost.context.resource import m_requires
from lampost.datastore.auto import AutoField
from lampost.datastore.dbo import CoreDBO, ChildDBO
from lampost.datastore.dbofield import DBOField
from lampost.datastore.exceptions import DataError
from lampost.datastore.meta import CommonMeta


m_requires(__name__, 'log', 'datastore')


approved_scripts = ()
script_cache = {}


def _post_init():
    global approved_scripts
    approved_scripts = fetch_set_keys('approved_scripts')


def create_chain(funcs):

    def chained(self, *args, **kwargs):
        last_return = None
        for func in funcs:
            last_return = func(self, *args, last_return=last_return, **kwargs)
        return last_return
    return chained


def compile_script(text, script_id):
    try:
        return compile(text, '{}_shadow'.format(script_id), 'exec'), None
    except SyntaxError as err:
        err_str = "Syntax Error: {}  text:{}  line: {}  offset: {}".format(err.msg, err.text, err.lineno, err.offset)
    except BaseException as err:
        err_str = "Script Error: {}".format(err.msg)
    debug(err_str)
    return None, err_str


def approve_script(script_hash, script_code):
    approved_scripts.add(script_hash)
    add_set_key('approved_scripts', script_hash)
    script_cache[script_hash] = script_code


def validate_script(script):
    try:
        return script_cache[script.script_hash]
    except KeyError:
        pass
    if script.script_hash not in approved_scripts:
        raise DataError
    code, _ = compile_script(script.text, script.dbo_id)
    if code:
        script_cache[script.script_hash] = code
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
    obj_type = DBOField('any')
    text = DBOField('', required=True)

    code = None
    _script_hash = None

    @property
    def script_hash(self):
        if not self._script_hash:
            hasher = hashlib.sha256()
            hasher.update(self.text.encode())
            self._script_hash = hasher.hexdigest()
        return self._script_hash

    def on_loaded(self):
        try:
            self.code = validate_script(self)
        except DataError:
            warn("Attempt to load unapproved script {}", self.dbo_id)

    @property
    def edit_dto(self):
        edit_dto = super().edit_dto
        edit_dto['approved'] = self.code is not None
        return edit_dto


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


class Scriptable(metaclass=CommonMeta):
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
