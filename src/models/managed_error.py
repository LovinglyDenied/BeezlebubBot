class ManagedCommandError(Exception):
    """An exception trown by getters and setters inside commands.
    When this error is trown, the ctx is already responded to.
    All that needs to happen is to quit out of the funcion"""
    pass