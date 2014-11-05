import sys

from lampost.context.context import Context

if __name__ != "__main__":
    print("Invalid usage")
    sys.exit(2)

context_args = {}
for arg in sys.argv[1:]:
    try:
        name, value = arg.split(":")
        context_args[name] = value
    except ValueError:
        print("Invalid argument format: %s" % arg)
        sys.exit(2)

Context(**context_args)

