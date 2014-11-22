import sys
from lampost.util.args import main_parser

if __name__ != "__main__":
    print("Invalid usage")
    sys.exit(2)

import importlib
try:
    importlib.import_module('lampost.util.log')
except ImportError:
    print("Unable to load lampost logging mods")
    sys.exit(2)



args = vars(main_parser.parse_args())

from lampost.context.context import Context
Context(**args)
