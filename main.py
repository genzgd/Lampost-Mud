import sys

if __name__ != "__main__":
    print("Invalid usage")
    sys.exit(2)

import importlib
try:
    importlib.import_module('lampost.util.log')
except ImportError:
    print("Unable to load lampost logging mods")
    sys.exit(2)

from lampost.context.context import Context

context_args = {}
for arg in sys.argv[1:]:
    try:
        name, value = arg.split(":")
        context_args[name] = value
    except ValueError:
        print("Invalid argument format: %s" % arg)
        sys.exit(2)

Context(**context_args)