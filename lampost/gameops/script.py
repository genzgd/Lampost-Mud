import os

from lampost.context.resource import m_requires, inject, provides
from lampost.datastore.dbo import RootDBO, DBOField
from lampost.gameops.action import item_action
from lampost.util.lmutil import Blank


m_requires('log', 'datastore', 'dispatcher', 'script_manager', __name__)


script_cache = {}


def _post_init():
    register('game_settings', configure_scripts)


def configure_scripts(settings):
    global root_area, exec_globals, script_dir
    root_area = getattr(settings, 'root_area', None)
    script_dir = getattr(settings,'script_dir', None)
    namespace = Blank()

    for dependency in ['log', 'datastore', 'dispatcher']:
        inject(namespace, dependency)
        delattr(namespace, dependency)

    exec_globals = namespace.__dict__
    script_manager.load_file_scripts()


@provides('script_manager')
class ScriptManager(object):
    def load_file_scripts(self):
        try:
            script_dirs = os.listdir(script_dir)
        except (EnvironmentError, TypeError):
            warn("Missing lampost_scripts directory")
            return
        for parent_name in script_dirs:
            if parent_name.startswith('_'):
                continue
            dir_name = 'lampost_scripts/{}'.format(parent_name)
            try:
                script_names = os.listdir(dir_name)
            except EnvironmentError:
                warn("Invalid directory {} in scripts directory".format(dir_name))
                continue
            for script_name in script_names:
                if script_name.startswith('_') or script_name.startswith('.'):
                    continue
                file_name = unicode('{}/{}'.format(dir_name, script_name))
                try:
                    with open(file_name) as script_file:
                        script_text = script_file.read()
                except EnvironmentError:
                    warn("Failed to read script file {}".format(file_name))
                    continue
                self.add_file_script(parent_name, script_name, script_text)

    def add_file_script(self, parent_name, script_name, text):
        if script_name.endswith('.py'):
            script_name = script_name[:-3]
        dbo_id = unicode("{}:{}".format(parent_name, script_name))
        script = load_object(Script, dbo_id)
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
            warn("Failed to compile file script {}".format(dbo_id))
            return
        script = create_object(Script, {'from_file': True, 'approved': True, 'dbo_id': dbo_id})
        script.code = code


def apply_script(host, script):
    script_globals = exec_globals.copy()
    script_globals['_host'] = host
    add_parent_globals(script_globals, host)

    exec_locals = {}
    try:
        exec(script.code, script_globals, exec_locals)
    except Exception:
        warn("Error applying script {}".format(script.dbo_id), exp)
        return
    for name, binding in exec_locals.viewitems():
        if hasattr(binding, '__call__'):
            orig_method = getattr(host, name, None)
            if orig_method:
                setattr(host, "{}_orig".format(name), orig_method)
            bound_method = binding.__get__(host)
            setattr(host, name, bound_method)
            if hasattr(binding, 'verbs'):
                host.self_providers.append(bound_method)
        else:
            setattr(host, name, binding)


def add_parent_globals(script_globals, host):
    if root_area:
        add_globals(load_object(Script, '{}:root'.format(root_area)), script_globals)
        if host.parent_id:
            add_globals(load_object(Script, '{}:{}'.format(root_area, host.parent_id)), script_globals)


def add_globals(script, script_globals):
    if not script:
        return
    if script.locals:
        script_globals.update(script.locals)
        return
    if script.compile():
        script.locals = {}
        try:
            exec(script.code, script_globals, script.locals)
            script_globals.update(script.locals)
        except Exception:
            del script.locals
            warn("Error applying global script {}".format(script.dbo_id), exp)



class Script(RootDBO):
    dbo_key_type = 'script'
    dbo_parent_type = 'area'

    dbo_rev = DBOField(0)
    title = DBOField('')
    text = DBOField('')
    approved = DBOField(False)
    from_file = DBOField(False)
    strong_ref = DBOField(False)
    file_name = DBOField("<dbo>")

    code = None
    locals = None

    @property
    def file_path(self):
        return "{}:{}".format(script_dir, self.parent_id).replace(':', '/')

    def compile(self):
        if not self.code:
            if self.from_file:
                self.load_from_file()
            if self.text:
                self._compile()
        return self.code

    def load_from_file(self):
        try:
            with open(self.file_path) as script_file:
                self.text = script_file.read()
        except EnvironmentError:
            warn("Failed to read script file {}".format(self.dbo_id))

    def _compile(self):
        try:
            self.code = compile(self.text, self.file_name, 'exec')
        except SyntaxError:
            log.error("Error compiling script {}".format(self.dbo_id))
            if self.code:
                del self.code
            return
        if self.strong_ref:
            script_cache.self[dbo_id] = self


class Scriptable(RootDBO):
    scripts = DBOField([], 'script')
    script_vars = DBOField({})

    def on_loaded(self):
        for script in self.scripts:
            if script.approved and script.compile():
                apply_script(self, script)
        self.post_script()

    def post_script(self):
        pass
