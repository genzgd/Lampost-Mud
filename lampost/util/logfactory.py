import inspect
import logging
from lampost.context.resource import provides
from lampost.util.log import root_logger, log_format


@provides('log')
class LogFactory():
    def __init__(self, init_level='WARN', filename=None):
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
        consumer.exception = logger.exception
        consumer.debug_enabled = lambda: logger.getEffectiveLevel() <= logging.DEBUG
        return logger