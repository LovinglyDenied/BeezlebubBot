import discord
from beartype import beartype
from beartype.typing import Callable, Any, Optional, Union

from .types import DiscordMember


class classproperty:
    """Decorator that effectivly combines the @classmethod and @property decorators.
    Those two cannot be combined by default (or, only in 3.8 - 3.10, with dropped support in 3.11)
    Yes, I could import an external library just for this, but this is only four lines of code..."""

    @beartype
    def __init__(self, fget: Callable):
        self.fget = fget

    @beartype
    def __get__(self, owner_self: Any, owner_cls: type):
        return self.fget(owner_cls)


@beartype
def mention_to_id(mention_string: str) -> int:
    """py-chord returns a mention-string for the discord.User and disord.Channel Option in commands
    This, according to the documentation, should not happen, but alas.
    this function transforms the string into something that can actually be used"""
    return int(mention_string.strip("<>@!#"))


@beartype
async def get_player_name(discord_id: int, *, bot: discord.ext.commands.Bot) -> str:
    """Gets the best match for the player name the bot can find"""
    player: Optional[DiscordMember] = bot.get_user(int(discord_id))
    if player:
        return str(player)

    try:
        player = await bot.fetch_user(int(discord_id))
        return str(player)
    except discord.NotFound:
        return f"User: {str(discord_id)}"
