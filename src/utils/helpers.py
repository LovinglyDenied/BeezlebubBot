from typing import Any, Callable


class classproperty:
    """Decorator that effectivly combines the @classmethod and @property decorators.
    Those two cannot be combined by default (or, only in 3.8 - 3.10, with dropped support in 3.11)
    Yes, I could import an external library just for this, but this is only four lines of code..."""

    def __init__(self, fget: Callable):
        self.fget = fget

    def __get__(self, owner_self: Any, owner_cls: type):
        return self.fget(owner_cls)


def mention_to_id(mention_string: str) -> int:
    """py-chord returns a mention-string for the discord.User and disord.Channel Option in commands
    This, according to the documentation, should not happen, but alas.
    this function transforms the string into something that can actually be used"""
    return int(mention_string.strip("<>@!#"))
