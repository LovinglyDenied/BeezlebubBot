from __future__ import annotations

import discord
from beartype import beartype
from beartype.typing import Protocol

from utils import MessageChannel
from .context_errors import ManagedCommandError, UnmanagedCommandError


class InvalidContext(Exception):
    """The paremeters provided did not create a valid ModelContext"""
    pass


class ModelContext(Protocol):
    """A basic context protocol, that all contexts should inherit from to keep feature-parity."""
    __slots__ = ()

    @property
    def bot(self) -> discord.ext.commands.Bot:
        """The main bot object of the context, such that any models can access it."""
        raise NotImplementedError

    async def exit(self, message: str) -> None:
        """The method to be called to respond to the context and raise a ManagedCommandError"""
        raise NotImplementedError


class ModelNoneCTX(ModelContext):
    """A model context that only trows an error.
    This should only be used if the error will be catched elsewhere."""
    __slots__ = ("_bot")

    @beartype
    def __init__(self, *, bot: discord.ext.commands.Bot):
        self._bot = bot

    @property
    @beartype
    def bot(self) -> discord.ext.commands.Bot:
        return self._bot

    @beartype
    async def exit(self, message: str) -> None:
        raise UnmanagedCommandError(message)

    @classmethod
    @beartype
    def from_other(cls, context: ModelContext):
        return cls(bot=context.bot)


class ModelACTX(ModelContext):
    """A ModelContext from a discord ApplicationContext"""
    __slots__ = ("ctx")

    @beartype
    def __init__(self, ctx: discord.ApplicationContext):
        self.ctx = ctx

    @property
    @beartype
    def bot(self) -> discord.ext.commands.Bot:
        return self.ctx.bot

    @beartype
    async def exit(self, message: str) -> None:
        await self.ctx.respond(message, ephemeral=True)
        raise ManagedCommandError


class ModelCCTX(ModelContext):
    """A ModelContext from a discord TextChannel & Bot"""
    __slots__ = ("channel", "_bot")

    @beartype
    def __init__(self, *, channel: MessageChannel, bot: discord.ext.commands.Bot):
        self.channel = channel
        self._bot = bot

    @property
    @beartype
    def bot(self) -> discord.ext.commands.Bot:
        return self._bot

    @beartype
    async def exit(self, message: str) -> None:
        from resources import create_error_embed
        embed: discord.Embed = create_error_embed(message)
        await self.channel.send(embed=embed)
        raise ManagedCommandError


class ModelVCTX(ModelContext):
    """A model context for a view, from a message & bot"""
    __slots__ = ("message", "_bot")

    @beartype
    def __init__(self, *, message: discord.Message, bot: discord.ext.commands.Bot):
        self.message = message
        self._bot = bot

    @property
    @beartype
    def bot(self) -> discord.ext.commands.Bot:
        return self._bot

    @beartype
    async def exit(self, message: str) -> None:
        from resources import create_error_embed
        embed: discord.Embed = create_error_embed(message)
        await self.message.reply(embed=embed, delete_after=60)
        raise ManagedCommandError
