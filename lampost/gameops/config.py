import sys
from collections import defaultdict


from lampost.context.resource import provides, m_requires
from lampost.datastore.dbo import DBOField, ParentDBO, ChildDBO, CoreDBO
from lampost.util.lputil import javascript_safe


m_requires(__name__, 'log', 'datastore', 'context')


_config_consumers = defaultdict(set)
_config_values = {}
_config_section_values = {}


def _register(cls, *config_properties):
    _config_consumers[cls].update(config_properties)
    if _config_values:
        set_config(cls, config_properties)


def configured(*config_properties):
    def wrapper(cls):
        _register(cls, *config_properties)
        return cls
    return wrapper


def m_configured(module_name, *config_properties):
    _register(sys.modules[module_name], *config_properties)


def set_config(consumer, properties):
    for prop in properties:
        try:
            if ":" in prop:
                property_name, value = prop.split(':')[1], _config_section_values[prop]
            else:
                property_name, value = prop, _config_values[prop]
        except KeyError:
            error("No value found for configuration value {} in consumer {}", prop, consumer.__name__)
            continue
        try:
            old_value = getattr(consumer, property_name)
            if old_value == value:
                return
            info("Updating config {} from {} to {} in {}.", property_name, old_value, value, consumer.__name__)
        except AttributeError:
            info("Setting config {}: {} in {}.", property_name, value, consumer.__name__)
        setattr(consumer, property_name, value)
    if hasattr(consumer, '_on_configured'):
        consumer._on_configured()


def update_all():
    for consumer, properties in _config_consumers.items():
        set_config(consumer, properties)


def create_from_dictionary(config_id, raw_configs, set_defaults=False):
    config = create_object(Config, {'dbo_id': config_id})

    sections = {}
    all_values = defaultdict(set)

    def init_section(section_name, section_dto=None):
        try:
            return sections[section_name]
        except KeyError:
            section_dto = section_dto or {}
            section_dto['dbo_id'] = '{}:{}'.format(config_id, section_name)
            section = create_object(ConfigSection, section_dto)
            sections[section_name] = section
            return section

    def add_raw(raw_config):
        for section_name, section_dto in raw_config.pop('sections', {}).items():
            init_section(section_name, section_dto)

        for section_name, settings in raw_config.items():
            section = init_section(section_name)
            setting_map = {setting.name: setting for setting in section.settings}
            for raw_setting in settings:
                new_setting = Setting().hydrate(raw_setting)
                if set_defaults:
                    new_setting.default = new_setting.value
                try:
                    existing = setting_map[new_setting.name]
                    warn("Setting {} with value {} overwritten by {}", setting.name, existing.value, setting.value)
                except KeyError:
                    pass
                setting_map[new_setting.name] = new_setting
                all_values[new_setting.name].add(section_name)
            section.settings = setting_map.values()
            save_object(section)

    for rc in raw_configs:
        add_raw(rc)

    for setting_name, section_names in all_values.items():
        if len(section_names) > 1:
            warn("Setting name {} found in multiple sections: {}", setting_name, ' '.join(section_names))

    return config


class Config(ParentDBO):
    dbo_key_type = 'config'
    dbo_set_key = 'configs'

    dbo_children_types = ['c_sect']

    def update_value(self, section, name, value):
        section = load_object('c_sect:{}:{}'.format(self.dbo_id, section))
        if section:
            for setting in section.settings:
                if setting.name == name:
                    setting.value = value
                    save_object(section)
                    return
        error("No setting found for {}:{}".format(section, name))

    def activate(self):
        _config_values.clear()
        _config_section_values.clear()
        for child_key in self.dbo_child_keys('c_sect'):
            section = load_object(child_key, ConfigSection)
            if section:
                for setting in section.settings:
                    _config_section_values['{}:{}'.format(section.name, setting.name)] = setting.value
                    if setting.name in _config_values:
                        warn("Duplicate value for {} found in section {}", setting.name, section.name)
                    else:
                        _config_values[setting.name] = setting.value
                        if setting.export:
                            context.set(setting.name, setting_value)

        update_all()


class ConfigSection(ChildDBO):
    dbo_key_type = 'c_sect'
    dbo_parent_type = 'config'

    name = DBOField()
    desc = DBOField()
    editor_constants = DBOField(False)
    settings = DBOField([], 'setting')


class Setting(CoreDBO):
    class_id = 'setting'
    name = DBOField()
    value = DBOField()
    desc = DBOField()
    default = DBOField()
    data_type = DBOField()
    min_value = DBOField()
    max_value = DBOField()
    step = DBOField(1)
    export = DBOField(False)


@provides('config_manager')
class ConfigManager():
    def __init__(self, config_id):
        self.config_id = config_id

    def start_service(self):
        self.config = load_object(Config, self.config_id)
        if self.config:
            self._dispatch_update()
        else:
            error("No configuration found")

    def save_config(self):
        save_object(self.config)

    def update_config(self, config_update):
        update_object(self.config, config_update)
        self._dispatch_update()

    def update_setting(self, setting_id, setting_value, setting_type='game'):
        setting_type = ''.join([setting_type, '_settings'])
        config_settings = getattr(self.config, setting_type)
        config_settings[setting_id] = setting_value

    def _session_connect(self, session):
        session.append({'client_config': {'default_displays': self.config.default_displays}})


    @property
    def name(self):
        return self.config.title

    @property
    def config_js(self):
        title = javascript_safe(self.config.title)
        description = javascript_safe(self.config.description)
        return "var lampost_config = {{title:'{0}', description:'{1}'}};".format(title, description)

    @property
    def config_json(self):
        return self.config.dto_value
