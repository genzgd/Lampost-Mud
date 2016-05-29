import sys

from importlib import import_module
from lampmud.setup import startargs
from lampost.util import logging
from lampost.di import resource

if __name__ != "__main__":
    print("Invalid usage")
    sys.exit(2)

args = startargs.main_parser.parse_args()
logging.init_config(args)
logging.root_logger.info("Started with args {}", args)

resource.register('log', logging.LogFactory())

import_module('lampost.di.importer')

from lampmud.setup import engine
engine.start(args)
