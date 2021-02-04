"""This module implements the singleton base class."""


import logging


_logger = logging.getLogger(__name__)


class Singleton():
    """
    Singleton base class.

    Any class that inherits from Singleton will be instantiated once.
    Any subsequent attempts to instantiate a Singleton will return the
    same object.

    Examples:
        >>> x = Singleton()
        >>> y = Singleton()
        >>> x is y
        True
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            _logger.debug("Creating singleton instance for class: "
                          % cls.__name__)
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance