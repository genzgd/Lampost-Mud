import sys

if __name__ != "__main__":
    print("Invalid usage")
    sys.exit(2)

import lampost.setup.args
args = lampost.setup.args.create_parser.parse_args()

if args.flush:
    response = input("Please confirm the database number you wish to clear: ")
    if response != str(args.db_num):
        print("Database numbers do not match")
        sys.exit(2)

import lampost.util.log
lampost.util.log.init_config(args)
lampost.util.log.root_logger.info("Started with args {}", args)

import lampost.setup.newsetup
lampost.setup.newsetup.new_setup(args)
