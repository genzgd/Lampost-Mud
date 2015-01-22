import sys

if __name__ != "__main__":
    print("Invalid usage")
    sys.exit(2)

from lampost.util import log
from lampost.setup import startargs

args = startargs.tools_parser.parse_args()

log.init_config(args)
log.root_logger.info("Started tools with args {}", args)

# We set the logging configuration before importing other modules so that the root logger is properly configured
from lampost.setup import tools

getattr(tools, args.op)(args)
