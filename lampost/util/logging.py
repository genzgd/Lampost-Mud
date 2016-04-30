import sys
import inspect
import logging

from logging import LogRecord, Logger


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


class LogFactory():
    def factory(self, consumer):
        if not inspect.ismodule(consumer):
            consumer = consumer.__class__
        logger = logging.getLogger(consumer.__name__)
        consumer.fatal = logger.fatal
        consumer.error = logger.error
        consumer.warn = logger.warn
        consumer.info = logger.info
        consumer.debug = logger.debug
        consumer.exception = logger.exception
        consumer.debug_enabled = lambda: logger.getEffectiveLevel() <= logging.DEBUG
        return logger


logging.setLoggerClass(LoggerFmt)
log_format = '{asctime: <20}  {levelname: <8} {name: <26}  {message}'


def init_config(args):
    global root_logger
    log_level = getattr(logging, args.log_level.upper())
    kwargs = {'format': log_format}
    if args.log_file:
        kwargs.update({'filename': args.log_file, 'filemode': args.log_mode})
    logging.basicConfig(level=log_level, style="{", **kwargs)
    root_logger = logging.getLogger('root')


def logged(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            root_logger.exception("Unhandled exception", func.__name__, error)
    return wrapper
