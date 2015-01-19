import sys

if __name__ != "__main__":
    print("Invalid usage")
    sys.exit(2)

from lampost.setup import startargs

args = startargs.main_parser.parse_args()

from lampost.util import log

log.init_config(args)
log.root_logger.info("Started with args {}", args)

from lampost.setup import engine
engine.start(args)
