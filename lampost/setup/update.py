from lampost.context.resource import m_requires
from lampost.setup.scripts import build_default_displays

m_requires('log', 'config_manager', 'perm', 'datastore', __name__)


def displays():
    config_manager.config.default_displays = build_default_displays()
    config_manager.save_config()











