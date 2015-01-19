from collections import defaultdict

from lampost.context.resource import m_requires
from lampost.datastore.dbo import DBOField, ParentDBO, ChildDBO, CoreDBO


m_requires(__name__, 'log', 'datastore')


def create(config_id, raw_configs, set_defaults=False):
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

    return create_object(Config, {'dbo_id': config_id})


class Config(ParentDBO):
    dbo_key_type = 'config'
    dbo_set_key = 'configs'

    dbo_children_types = ['c_sect']

    def update_value(self, section, name, value):
        section = load_object('c_sect:{}:{}'.format(self.dbo_id, section))
        if section:
            self.section_values['{}:{}'.format(section, name)] = value
            for setting in section.settings:
                if setting.name == name:
                    setting.value = value
                    save_object(section)
                    return
        error("No setting found for {}:{}".format(section, name))

    def on_loaded(self):
        self.section_values = {}
        self.exports = {}
        for child_key in self.dbo_child_keys('c_sect'):
            section = load_object(child_key, ConfigSection)
            if section:
                for setting in section.settings:
                    self.section_values['{}:{}'.format(section.child_id, setting.name)] = setting.value


class ConfigSection(ChildDBO):
    dbo_key_type = 'c_sect'
    dbo_parent_type = 'config'

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
