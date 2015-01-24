import sys

if __name__ != "__main__":
    print("Invalid usage")
    sys.exit(2)

import lampost.setup.args
args = lampost.setup.args.main_parser.parse_args()

import lampost.util.log
lampost.util.log.init_config(args)
lampost.util.log.root_logger.info("Started with args {}", args)

import lampost.context.context
lampost.context.context.Context(args)
