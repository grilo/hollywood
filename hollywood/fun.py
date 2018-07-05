#!/usr/bin/env python
# Inspired by guido: https://www.artima.com/weblogs/viewpost.jsp?thread=101605
# With help for object methods from: https://stackoverflow.com/questions/6009344

"""
    WARNING: Does **NOT** work on functions, only methods (class and instance).


    Provides pattern matching-like utility to class methods. It's a much
    inferior solution to true functional pattern matching, only works with
    basic types and has no support for types within types.

    Meaning @patternmatch([int]) doesn't really work, considers only list
    as the type.

    Example:

        class Hello(object):

            @patternmatch(int)
            def something(self, arg):
                print "This will print the integer", arg

            @patternmatch(str)
            def something(self, arg):
                print "This will print the string", arg

            @patternmatch(int, int)
            def something(self, arg, arg)
                print "This will print two integers", arg, arg

            def something(self, *args):
                print "This will match everything else."


        a = Hello()
        a.something(10)
        a.something('world')
        a.something(20, 30)
        a.something(10, 'world', '30')

    In addition:
        - Supports user-defined types:
            @patternmatch(hollywood.net.http.Request)
        - The number of arguments in the decorator must be an exact match for
          the number of arguments in the method.
        - No **kwargs (an anti-pattern anyways when using this style).
"""

class MultiMethod(object):

    registry = {}

    def __init__(self, name):
        self.name = name
        self.typemap = {}
    def __call__(self, *args):
        types = tuple(arg.__class__ for arg in args[1:])
        function = self.typemap.get(types)
        if function is None:
            raise TypeError("No match: %s %s" % (self.name, types))
        return function(*args)

    def register(self, types, function):
        if types in self.typemap:
            raise TypeError("Duplicate registration: %s %s" % (self.name, types))
        self.typemap[types] = function

def patternmatch(*types):
    def register(function):
        function = getattr(function, "__lastreg__", function)
        name = function.__name__
        mm = MultiMethod.registry.get(name)
        if mm is None:
            mm = MultiMethod.registry[name] = MultiMethod(name)
        mm.register(types, function)
        mm.__lastreg__ = function
        def getter(instance, *args, **kwargs):
            return mm(instance, *args, **kwargs)
        return getter
    return register

# Aliases
def handle(*types):
    return patternmatch(*types)
def match(*types):
    return patternmatch(*types)
