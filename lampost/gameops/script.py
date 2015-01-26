import bisect
from collections import defaultdict
import inspect
import os
import types
from types import CodeType
from weakref import WeakKeyDictionary

from lampost.context.resource import m_requires, inject
from lampost.datastore.auto import AutoField
from lampost.datastore.dbo import ChildDBO, CoreDBO
from lampost.datastore.dbofield import DBOField
from lampost.datastore.meta import CommonMeta
from lampost.gameops.action import obj_action
from lampost.util.lputil import Blank


m_requires(__name__, 'log', 'datastore', 'dispatcher', 'script_manager')


script_cache = {}


class ScriptManager():

    def _post_init(self):
        register('game_settings', self.configure_scripts)

    def configure_scripts(self, settings):
        global root_area, exec_globals, script_dir
        root_area = settings.get('root_area', 'immortal')
        script_dir = settings.get('script_dir', 'lampost_scripts')
        namespace = Blank()

        for dependency in ['log', 'datastore', 'dispatcher']:
            inject(namespace, dependency)
            delattr(namespace, dependency)

        exec_globals = namespace.__dict__
        exec_globals['item_action'] = obj_action
        self.load_file_scripts()

    def load_file_scripts(self):
        try:
            script_dirs = os.listdir(script_dir)
        except (EnvironmentError, TypeError):
            warn("Missing lampost_scripts directory {}", script_dir)
            return
        for parent_name in script_dirs:
            if parent_name.startswith('_'):
                continue
            dir_name = '{}/{}'.format(script_dir, parent_name)
            try:
                script_names = os.listdir(dir_name)
            except EnvironmentError:
                warn("Invalid directory {} in scripts directory", dir_name)
                continue
            for script_name in script_names:
                if script_name.startswith('_') or script_name.startswith('.'):
                    continue
                file_name = '{}/{}'.format(dir_name, script_name)
                try:
                    with open(file_name) as script_file:
                        script_text = script_file.read()
                except EnvironmentError:
                    warn("Failed to read script file {}", file_name)
                    continue
                self.add_file_script(parent_name, script_name, script_text)

    def add_file_script(self, parent_name, script_name, text):
        info("Loading script {}:{}", parent_name, script_name)
        if script_name.endswith('.py'):
            script_name = script_name[:-3]
        dbo_id = "{}:{}".format(parent_name, script_name)
        script = load_object(dbo_id, Script)
        if script:
            if script.from_file:
                if not script.approved:
                    script.approved = True
                    save_object(script)
                    if script.strong_ref:
                        script_cache[dbo_id] = script
            else:
                warn("Existing script not marked from file")
            return
        try:
            code = compile(text, dbo_id, 'exec')
        except SyntaxError:
            warn("Failed to compile file script {}", dbo_id, exc_info=True)
            return
        info("Creating script")
        script = create_object(Script, {'from_file': True, 'approved': True, 'dbo_id': dbo_id})
        script.code = code

    def delete_script(self, script):
        script_cache.pop(script.dbo_id, None)


def apply_script(host, script):
    script_globals = exec_globals.copy()
    script_globals['_host'] = host
    add_parent_globals(script_globals, host)

    exec_locals = {}
    try:
        exec(script.code, script_globals, exec_locals)
    except Exception:
        warn("Error applying script {}".format(script.dbo_id), __name__, exp)
        return
    for name, binding in exec_locals.items():
        if hasattr(binding, '__call__'):
            orig_method = getattr(host, name, None)
            if orig_method:
                setattr(host, "{}_orig".format(name), orig_method)
            bound_method = binding.__get__(host)
            setattr(host, name, bound_method)
            if hasattr(binding, 'verbs'):
                host.instance_providers.append(bound_method)
        else:
            setattr(host, name, binding)


def add_parent_globals(script_globals, host):
    if root_area:
        add_globals(load_object('{}:root'.format(root_area), Script, True), script_globals)
        if getattr(host, 'dbo_parent_type', None):
            add_globals(load_object('{}:{}'.format(root_area, host.dbo_parent_type), Script, True), script_globals)


def add_globals(script, script_globals):
    if not script:
        return
    if script.namespace:
        script_globals.update(script.namespace)
        return
    if script.compile():
        script.namespace = {}
        try:
            exec(script.code, script_globals, script.namespace)
            script_globals.update(script.namespace)
        except BaseException:
            del script.namespace
            warn("Error applying global script {}", script.dbo_id, exc_info=True)


class Script(ChildDBO):
    dbo_key_type = 'script'
    dbo_parent_type = 'area'

    title = DBOField('')
    text = DBOField('')
    approved = DBOField(False)
    from_file = DBOField(False)
    strong_ref = DBOField(False)
    file_error = DBOField()
    compile_error = DBOField()

    code = None
    namespace = None
    live_text = None

    @property
    def file_path(self):
        return "{}:{}.py".format(script_dir, self.dbo_id).replace(':', '/')

    @property
    def file_name(self):
        if self.from_file:
            return self.file_path
        return "<dbo:{}>".format(self.dbo_id)

    def compile(self):
        if not self.code:
            if not self.live_text:
                if self.from_file:
                    self.load_from_file()
                else:
                    self.live_text = self.text
            if self.live_text:
                self._compile()
        return self.code

    def load_from_file(self):
        if not self.title:
            self.title = self.file_path
        try:
            with open(self.file_path) as script_file:
                self.live_text = script_file.read()
                self.file_error = None
        except EnvironmentError as exp:
            warn("Failed to read script file {}", self.dbo_id)
            self.live_text = ''
            self.file_error = str(exp)
            if self.code:
                del self.code
            save_object(self)

    def write(self, new_text):
        with open(self.file_path, 'w') as script_file:
            script_file.write(new_text)

    @property
    def dto_value(self):
        self.compile()
        dto_value = super().dto_value
        del dto_value['text']
        dto_value['live_text'] = self.live_text
        return dto_value

    def _compile(self):
        try:
            self.code = compile(self.live_text, self.file_name, 'exec')
            self.compile_error = None
            if self.strong_ref:
                script_cache.self[dbo_id] = self
        except SyntaxError as exp:
            self.compile_error = str(exp)
            error("Error compiling script {}", self.dbo_id)
            if self.code:
                del self.code


def create_chain(funcs):

    def chained(self, *args, **kwargs):
        last_return = None
        for func in funcs:
            last_return = func(self, *args, last_return=last_return, **kwargs)
        return last_return
    return chained


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
    code = None

    def __cmp__(self, other):
        if self.priority < other.priority:
            return -1
        if self.priority > other.priority:
            return 1
        return 0

    def compile(self):
        if not self.code:
            try:
                self.code = compile(self.text, '{}_shadow'.format(self.name), 'exec')
            except SyntaxError:
                warn("Failed to compile shadow script {}", self.name, exc_info=True)
                return False
        return True


class Scriptable(metaclass=CommonMeta):
    scripts = DBOField([], 'script')
    script_vars = DBOField({})
    shadows = DBOField([], 'shadow_script')
    shadow_chains = AutoField({})

    def on_loaded(self):
        chains = defaultdict(list)
        for shadow in self.shadows:
            if shadow.compile():
                func_shadows = chains[shadow.name]
                bisect.insort(func_shadows, shadow)
        self.shadow_chains = chains
        self.load_scripts()

    @Shadow
    def load_scripts(self):
        pass



