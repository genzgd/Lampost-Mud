import os

from lampost.context.resource import m_requires, inject, provides
from lampost.datastore.dbo import RootDBO, DBOField
from lampost.gameops.action import obj_action
from lampost.mud.action import imm_action
from lampost.util.lmutil import Blank


m_requires(__name__, 'log', 'datastore', 'dispatcher', 'script_manager')


script_cache = {}


@provides('script_manager')
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
        except (EnvironmentError, TypeError) as exp:
            warn("Missing lampost_scripts directory", __name__, exp)
            return
        for parent_name in script_dirs:
            if parent_name.startswith('_'):
                continue
            dir_name = '{}/{}'.format(script_dir, parent_name)
            try:
                script_names = os.listdir(dir_name)
            except EnvironmentError:
                warn("Invalid directory {} in scripts directory".format(dir_name))
                continue
            for script_name in script_names:
                if script_name.startswith('_') or script_name.startswith('.'):
                    continue
                file_name = '{}/{}'.format(dir_name, script_name)
                try:
                    with open(file_name) as script_file:
                        script_text = script_file.read()
                except EnvironmentError:
                    warn("Failed to read script file {}".format(file_name))
                    continue
                self.add_file_script(parent_name, script_name, script_text)

    def add_file_script(self, parent_name, script_name, text):
        info("Loading script {}:{}".format(parent_name, script_name))
        if script_name.endswith('.py'):
            script_name = script_name[:-3]
        dbo_id = "{}:{}".format(parent_name, script_name)
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
    except BaseException as exp:
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
        add_globals(load_by_key('script', '{}:root'.format(root_area), True), script_globals)
        if getattr(host, 'dbo_parent_type', None):
            add_globals(load_by_key('script', '{}:{}'.format(root_area, host.dbo_parent_type), True), script_globals)


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
            warn("Failed to read script file {}".format(self.dbo_id), __name__, exp)
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
            log.error("Error compiling script {}".format(self.dbo_id))
            if self.code:
                del self.code


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


@imm_action('load_file_scripts', imm_level='supreme')
def load_file_scripts(**_):
    script_manager.load_file_scripts()


@imm_action('scripts', 'scripts', 'admin')
def show_scripts(source, target, **_):
    if not target.scripts:
        return "No scripts"
    source.display_line("Scripts: ")
    for script in target.scripts:
        source.display_line("    {}".format(script.title))
