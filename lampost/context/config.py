import glob
import sys
import logging
import yaml

from collections import defaultdict

log = logging.getLogger(__name__)

_consumer_map = defaultdict(set)
_value_map = {}
_section_value_map = {}


def m_configured(module_name, *config_properties):
    _register(sys.modules[module_name], *config_properties)


def configured(*config_properties):
    def wrapper(cls):
        original_init = cls.__init__

        def init_and_register(self, *args, **kwargs):
            _register(self, *config_properties)
            original_init(self, *args, **kwargs)

        cls.__init__ = init_and_register
        return cls

    return wrapper


def _register(cls, *config_properties):
    _consumer_map[cls].update(config_properties)
    if _value_map:
        inject_config(cls, config_properties)


def get_value(property_name):
    if ":" in property_name:
        return _section_value_map[property_name]
    return _value_map[property_name]


def inject_config(consumer, properties):
    for prop in properties:
        try:
            if ":" in prop:
                property_name, value = prop.split(':')[1], _section_value_map[prop]
            else:
                property_name, value = prop, _value_map[prop]
        except KeyError:
            log.error("No value found for configuration value {} in consumer {}", prop, consumer.__name__)
            continue
        try:
            old_value = getattr(consumer, property_name)
            if old_value == value:
                return
            log.info("Updating config {} from {} to {} in {}.", property_name, old_value, value, consumer.__name__)
        except AttributeError:
            log.info("Setting config {}: {} in {}.", property_name, value, consumer.__name__)
        setattr(consumer, property_name, value)
    if hasattr(consumer, '_on_configured'):
        consumer._on_configured()


def update_all():
    for consumer, properties in _consumer_map.items():
        inject_config(consumer, properties)


def load_yaml(path):
    all_config = []

    for file_name in glob.glob("{}/*yaml".format(path)):
        with open(file_name, 'r') as yf:
            log.info("Processing config file {}", file_name)
            try:
                yaml_load = yaml.load(yf)
                all_config.append(yaml_load)
            except yaml.YAMLError:
                log.exception("Error parsing {}", yf)

    return all_config


def activate(all_values):
    _section_value_map.clear()
    _value_map.clear()
    for section_key, value in all_values.items():
        _section_value_map[section_key] = value
        value_key = section_key.split(':')[1]
        if value_key in _value_map:
            log.warn("Duplicate value for {} found in section {}", value_key, section_key.split(':')[0])
        else:
            _value_map[value_key] = value
    update_all()
    return _value_map
