import sys

from lampost.setup import startargs
from lampost.util import logging


if __name__ != "__main__":
    print("Invalid usage")
    sys.exit(2)

args = startargs.main_parser.parse_args()
logging.init_config(args)
logging.root_logger.info("Started with args {}", args)

from lampost.di import resource
resource.register('log', logging.LogFactory())

from lampmud.setup import engine
engine.start(args)
