#!/usr/bin/env python

"""
    Exceptions module, all generic actor-related exceptions are found here.

    Doesn't include exceptions for specific actor implementations.
"""

class ActorNotRegisteredError(Exception):
    """
        When the actor was attempted to be used but it's not yet registered.

        This might occur if the actor's module isn't imported before invoking
        actor.System.init().
    """
    pass

class ActorRuntimeError(Exception):
    """
        When an actor's "receive" method raises any exception.

        Should be used by the Supervisor to restart the actor.
    """
    pass
