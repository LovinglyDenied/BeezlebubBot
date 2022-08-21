from discord.ext.commands import CommandError


class ManagedCommandError(CommandError):
    """An exception trown by getters and setters inside commands.
    When this error is trown, the context is already responded to.
    All that needs to happen is to quit out of the funcion"""
    pass

class UnmanagedCommandError(CommandError):
    """An exception trown by getters and setters inside commands.
    When this error is trown, the context is not jet responded to."""
    pass
