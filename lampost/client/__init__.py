import pkgutil

for loader, name, is_pkg in pkgutil.walk_packages(__path__):
    loader.find_module(name).load_module(name)
