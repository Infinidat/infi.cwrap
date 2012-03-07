__import__("pkg_resources").declare_namespace(__name__)

""" working with ctypes is hard. specifically, wrapping functions is hard.
this module helps you do that.
"""

import ctypes
import os

IN = 1
OUT = 2
IN_OUT = 3

def get_os_name():
    """ returns one of 'windows', 'linux', 'sunos', 'hpux', 'aix', 'darwin'
    """
    import platform
    os_name = platform.system().lower()
    os_name = os_name.replace("-", "")
    return os_name

def errcheck_zero():
    """ this error checker raises a RuntimeError if the returned value is zero
    """
    def errcheck(result, func, args):
        if result == 0:
            raise RuntimeError(result)
        return args
    return errcheck

def errcheck_nonzero():
    """ this error checker raises a RuntimeError if the returned value is non-zero
    """
    def errcheck(result, func, args):
        if result != 0:
            raise RuntimeError(result)
        return args
    return errcheck

def errcheck_nothing():
    """ this error checker raises no exception
    """
    def errcheck(result, func, args):
        return args
    return errcheck

def _build_args_for_functype(return_value, parameters):
    args = (return_value,)
    for parameter_tuple in parameters:
        args += (parameter_tuple[0],)
    return args

def _build_paramflags_for_prototype(parameters):
    paramflags = tuple()
    for parameter_tuple in parameters:
        paramflags += (parameter_tuple[1:],)
    return paramflags

def wrap_library_function(name, library, function_type, return_value=ctypes.c_ulong, parameters=(), 
                          errcheck=errcheck_nonzero()):
    """ this function wraps C library functions
    name            function name
    library
    function_type   string WINFUNCTYPE or CFUNCTYPE
    return_value    ctypes type
    parameters      tuple of the following form:
                    (ctypes_type, in/out, name, default_value)
    errcheck
    """
    args = _build_args_for_functype(return_value, parameters)
    function_type = getattr(ctypes, function_type)
    function_prototype = function_type(*args)
    _paramflags = _build_paramflags_for_prototype(parameters)
    _function = function_prototype((name, library), _paramflags)
    _function.errcheck = errcheck
    return _function

class WrappedFunction(object):
    """ wrapping class for functions from shared libraries

    In order to wrap funtion named "thisFunction" from shared library "sharedLibrary.so",
    create a new class thisFunction that inherits from this class, and have the classmethod
    get_library_name return the filename of the shared library to load.
    The class method _get_library calls ctype's LoadLibrary method with what _get_library_name returns.

    Do not that on UNIX systems, get_library_name requires to return a full path


    an usage example:
    """

    # default return value is ctypes.c_ulong
    # change if necessary when inherting
    return_value = ctypes.c_ulong

    @classmethod
    def get_parameters(cls):
        """ Each item in this tuple contains further information about a parameter, it must be a tuple containing one, two, or three items.

        The first item is an integer containing a combination of direction flags for the parameter:

        1
        Specifies an input parameter to the function.
        2
        Output parameter. The foreign function fills in a value.
        4
        Input parameter which defaults to the integer zero.
        The optional second item is the parameter name as string. If this is specified, the foreign function can be called with named parameters.

        The optional third item is the default value for this parameter.
        """
        raise NotImplementedError

    @classmethod
    def get_errcheck(cls):
        """ returns a function that is called to check the returned value of the wrapped function.
        The error-checking function gets the following arguments from ctypes: result, func, args.
        and should return args or raise an exception.
        """
        return errcheck_nonzero()

    @classmethod
    def get_library_name(cls):
        """ returns the name of the shared library to load
        """
        raise NotImplementedError

    @classmethod
    def _get_library(cls):
        try:
            return getattr(ctypes.windll, cls.get_library_name())
        except:
            raise OSError

    @classmethod
    def __new__(cls, *args, **kwargs):
        function = cls._get_function()
        return_value = function(*args[1:], **kwargs)
        return return_value

    @classmethod
    def _get_function(cls):
        parameters = cls.get_parameters()
        function = wrap_library_function(cls.__name__, cls._get_library(), cls._get_function_type(), 
                                         cls.return_value, parameters, cls.get_errcheck())
        return function

    @classmethod
    def is_available_on_this_platform(cls):
        try:
            function = cls._get_function()
            return True
        except (AttributeError, OSError, NotImplementedError):
            return False
        return True # pragma: no cover

    @classmethod
    def _get_function_type(cls):
        return 'WINFUNCTYPE' if os.name == 'nt' else 'CFUNCTYPE'
