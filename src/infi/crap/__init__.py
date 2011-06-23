__import__("pkg_resources").declare_namespace(__name__)

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
    def errcheck(result, func, args):
        if result == 0:
            raise RuntimeError(result)
        return args
    return errcheck

def errcheck_nonzero():
    def errcheck(result, func, args):
        if result != 0:
            raise RuntimeError(result)
        return args
    return errcheck

def errcheck_nothing():
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

def wrap_library_function(name, library, return_value=ctypes.c_ulong, parameters=(), errcheck=errcheck_nonzero()):
    """ this function wraps C library functions
    name            function name
    return_value    ctypes type
    parameters      tuple of the following form:
                    (ctypes_type, in/out, name, default_value)
    """
    args = _build_args_for_functype(return_value, parameters)
    function_type = getattr(ctypes, 'WINFUNCTYPE') if os.name == 'nt' else getattr(ctypes, 'CFUNCTYPE')
    function_prototype = function_type(*args)
    _paramflags = _build_paramflags_for_prototype(parameters)
    _function = function_prototype((name, library), _paramflags)
    _function.errcheck = errcheck
    return _function

class WrappedFunction(object):
    _return_value = ctypes.c_ulong

    @classmethod
    def _get_errcheck(cls):
        return errcheck_nonzero()

    @classmethod
    def _get_library(cls):
        raise NotImplementedError

    @classmethod
    def _get_parameters(cls):
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
    def __new__(cls, *args, **kwargs):
        function = cls._get_function()
        return_value = function(*args[1:], **kwargs)
        return return_value

    @classmethod
    def _get_function(cls):
        name = cls.__name__
        parameters = cls._get_parameters()
        function = wrap_library_function(cls.__name__, cls._get_library(), cls._return_value,
                                         parameters, cls._get_errcheck())
        return function

    @classmethod
    def is_available_on_this_platform(cls):
        try:
            function = cls._get_function()
            return True
        except (AttributeError, OSError):
            return False
        return True # pragma: no cover

