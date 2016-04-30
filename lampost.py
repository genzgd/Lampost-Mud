import sys

from lampost.setup import startargs
from lampost.util import logging
from lampost.context import resource

if __name__ != "__main__":
    print("Invalid usage")
    sys.exit(2)

args = startargs.main_parser.parse_args()
logging.init_config(args)
logging.root_logger.info("Started with args {}", args)

resource.register('log', logging.LogFactory())


from lampost.setup import engine
engine.start(args)
