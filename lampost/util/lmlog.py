import traceback

from sys import stdout
from datetime import datetime
from lampost.context.resource import m_requires, provides, get_resource

m_requires('dispatcher', __name__)

LOG_LEVELS = {"fatal": 0, "error": 10, "warn": 20, "info": 30, "debug": 40}


def logged(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            get_resource("log").error("Unhandled exception", func, error)
    return wrapper


@provides('log', True)
class Log(object):

    def __init__(self, log_level, file_name=None):
        if file_name:
            self.output = open(file_name, 'w')
        else:
            self.output = stdout
        self.level_desc = "Not set"
        self._set_level(log_level)

    def _set_level(self, log_level):
        log_level = log_level.lower()
        if LOG_LEVELS.get(log_level) is not None:
            self.level = LOG_LEVELS[log_level]
            self.debug("Log level set to {}".format(log_level))
            self.level_desc = log_level
        else:
            self.level = LOG_LEVELS["info"]
            self.level_desc = "info"
            self.warn("Invalid log level {}".format(log_level))

    def _log(self, log_level, log_msg, log_name, exception):
        if LOG_LEVELS[log_level] > self.level:
            return
        if not isinstance(log_name, str):
            log_name = log_name.__class__.__name__
        log_entry = "{} {}: -{}- {}\n".format(log_level, datetime.now(), log_name, log_msg)
        self.output.write(log_entry)
        if exception:
            self.output.write(traceback.format_exc())
        self.output.flush()
        try:
            dispatch("log", log_entry)
        except NameError:
            pass
        return log_msg

    def fatal(self, log_msg, log_name="root", exception=None):
        self._log('fatal', log_msg, log_name, exception)

    def error(self, log_msg, log_name="root", exception=None):
        self._log('error', log_msg, log_name, exception)

    def warn(self, log_msg, log_name="root", exception=None):
        self._log('warn', log_msg, log_name, exception)

    def info(self, log_msg, log_name="root", exception=None):
        self._log('info', log_msg, log_name, exception)

    def debug(self, log_msg, log_name="root", exception=None):
        self._log('debug', log_msg, log_name, exception)

