from importlib import import_module

from lampost.context.config import m_configured
from lampost.context.resource import m_requires


import_module('lampost.model.area')
import_module('lampost.mud.immortal')
import_module('lampost.comm.chat')
import_module('lampost.mud.inventory')
import_module('lampost.mud.socials')
import_module('lampost.mud.group')
import_module('lampost.env.instance')


def first_time_setup(flavor):
    pass

