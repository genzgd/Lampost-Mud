import time
import json

pronouns = {'none': ['it', 'it', 'its', 'itself', 'its'],
            'male': ['he', 'him', 'his', 'himself', 'his'],
            'female': ['she', 'her', 'her', 'herself', 'hers']}


def l_just(value, size):
    return value.ljust(size).replace(' ', '&nbsp;')


def timestamp(record):
    ts = int(time.time())
    try:
        record['timestamp'] = ts
        return record
    except KeyError:
        return ':'.join([record, ts])


def plural(noun):
    if noun[-1:] == 's':
        return "{}es".format(noun)
    return "{}s".format(noun)

def dump(dump_dict):
    return ["{0}: {1}".format(key, str(value)) for key, value in dump_dict.iteritems()]


def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start + len(needle))
        n -= 1
    return start


def find_extra_prep(prep, command):
    start_ix = find_nth(command, prep, 1)
    return command[start_ix + len(prep) + 1:]


def find_extra(verb, used_args, command):
    verb_len = len(verb)
    try:
        arg_len = len(used_args)
    except TypeError:
        arg_len = used_args
    find_loc = find_nth(command, " ", arg_len + verb_len)
    if find_loc == -1:
        return None
    return command[find_loc + 1:]


def javascript_safe(value):
    value = value.replace('"', '\\\"')
    value = value.replace("'", "\\'")
    value = value.replace("\n", "")
    return value


class Blank(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class PermError(Exception):
    pass


class StateError(Exception):
    def __init__(self, message):
        self.message = message


class PatchError(Exception):
    def __init__(self, message):
        self.message = message


def cls_name(cls):
    return ".".join([cls.__module__, cls.__name__])


def patch_object(obj, prop, new_value):
    existing_value = getattr(obj, prop, None)
    if existing_value is not None:
        try:
            if isinstance(existing_value, int):
                new_value = int(new_value)
            elif isinstance(existing_value, long):
                new_value = long(new_value)
            elif isinstance(existing_value, float):
                new_value = float(new_value)
            elif isinstance(existing_value, basestring):
                pass
            else:
                raise PatchError("Only number and string values can be patched")
        except ValueError:
            raise PatchError("Existing value is not compatible with patch value")
    try:
        setattr(obj, prop, new_value)
    except:
        raise PatchError("Failed to set value.")


def str_to_primitive(value):
    if value == 'None':
        return None
    try:
        return json.JSONDecoder().decode(value)
    except ValueError:
        pass
    return json.JSONDecoder().decode('"{}"'.format(value))


def args_print(**kwargs):
    return ''.join(['{0}:{1} '.format(key, str(value)) for key, value in kwargs.iteritems()])
