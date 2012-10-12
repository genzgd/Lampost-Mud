import sys
from lampost.context.setup import SetupMudContext

if __name__ != "__main__":
    print "Invalid usage"
    sys.exit(2)

context_args = {}
for arg in sys.argv[1:]:
    try:
        name, value = arg.split(":")
        context_args[name] = value
    except ValueError:
        print "Invalid argument format: %s" % arg
        sys.exit(2)

if not context_args.get('imm_name'):
    print "Please supply an imm_name argument to identify the root user"
    sys.exit(2)

SetupMudContext(**context_args)
