import sys

from lampost.util import logging
from lampost.di.resource import register
from lampost.setup import startargs

if __name__ != "__main__":
    print("Invalid usage")
    sys.exit(2)


args = startargs.create_parser.parse_args()

# We set the logging configuration before importing other modules so that the root logger is properly configured
logging.init_config(args)
logging.root_logger.info("Started with args {}", args)
register('log', logging.LogFactory())

from lampost.setup import newsetup

if args.flush:
    response = input("Please confirm the database number you wish to clear: ")
    if response != str(args.db_num):
        print("Database numbers do not match")
        sys.exit(2)

newsetup.new_setup(args)
