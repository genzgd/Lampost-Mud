from lampost.context.resource import m_requires
from lampost.context.config import m_configured

m_requires(__name__, 'dispatcher')

client_displays = {}

def _on_configured():
    client_displays.clear()
    for display in default_displays:
        client_displays[display['name']] = display['value']

m_configured(__name__, 'default_displays')


def _post_init():
    register('session_connect', set_displays)


def set_displays(session):
    session.append({'client_config': {'default_displays': client_displays}})

