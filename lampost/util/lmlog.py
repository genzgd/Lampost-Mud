import logging
import inspect
from logging import LogRecord, Logger

from lampost.context.resource import provides


class LogFmtRecord(LogRecord):
    def getMessage(self):
        msg = self.msg
        if self.args:
            if isinstance(self.args, dict):
                msg = msg.format(self.args)
            else:
                msg = msg.format(*self.args)
        return msg


class LoggerFmt(Logger):
    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
        rv = LogFmtRecord(name, level, fn, lno, msg, args, exc_info, func, sinfo)
        if extra is not None:
            for key in extra:
                if (key in ["message", "asctime"]) or (key in rv.__dict__):
                    raise KeyError("Attempt to overwrite %r in LogRecord" % key)
                rv.__dict__[key] = extra[key]
        return rv


logging.setLoggerClass(LoggerFmt)
log_format = '{asctime} {levelname} {message}'
root_logger = logging.getLogger('root')


def logged(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            root_logger.exception("Unhandled exception", func.__name__, error)
    return wrapper


@provides('log')
class LogFactory():
    def __init__(self, init_level='TESTME', filename=None):
        log_level = getattr(logging, init_level.upper(), None)
        if not isinstance(log_level, int):
            root_logger.warn("Invalid log level {init_level} specified", init_level=initlevel)
            log_level = logging.WARN
        logging.basicConfig(level=log_level, style='{', filename=filename, format=log_format)

    def factory(self, consumer):
        if not inspect.ismodule(consumer):
            consumer = consumer.__class__
        logger = logging.getLogger(consumer.__name__)
        consumer.fatal = logger.fatal
        consumer.error = logger.error
        consumer.warn = logger.warn
        consumer.info = logger.info
        consumer.debug = logger.debug
        consumer.debug_enabled = lambda: logger.getEffectiveLevel() <= logging.DEBUG
        return logger






