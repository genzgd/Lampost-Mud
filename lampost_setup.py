import sys

if __name__ != "__main__":
    print("Invalid usage")
    sys.exit(2)

from lampost.util import log
from lampost.setup import startargs

args = startargs.create_parser.parse_args()

log.init_config(args)
log.root_logger.info("Started with args {}", args)

# We set the logging configuration before importing other modules so that the root logger is properly configured
from lampost.setup import newsetup

if args.flush:
    response = input("Please confirm the database number you wish to clear: ")
    if response != str(args.db_num):
        print("Database numbers do not match")
        sys.exit(2)

newsetup.new_setup(args)
