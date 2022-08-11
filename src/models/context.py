from __future__ import annotations

from typing import Protocol

import discord

from .managed_error import ManagedCommandError


class InvalidContext(Exception):
    """The paremeters provided did not create a valid ModelContext"""
    pass


class ModelContext(Protocol):
    """A basic context protocol, that all contexts should inherit from to keep feature-parity."""
    __slots__ = ()

    @property
    def bot(self) -> discord.ext.commands.Bot:
        """The main bot object of the context"""
        raise NotImplementedError

    async def exit(self, message: str) -> None:
        """The method to be called to respond to the context and raise a ManagedCommandError"""
        raise NotImplementedError


class ModelACTX(ModelContext):
    """A ModelContext from a discord ApplicationContext"""
    __slots__ = ("ctx")

    def __init__(self, ctx: discord.ApplicationContext):
        if not isinstance(ctx, discord.ApplicationContext):
            raise InvalidContext
        self.ctx = ctx

    @property
    def bot(self) -> discord.ext.commands.Bot:
        return self.ctx.bot

    async def exit(self, message: str) -> None:
        await self.ctx.respond(message, ephemeral=True)
        raise ManagedCommandError


class ModelCCTX(ModelContext):
    """A ModelContext from a discord TextChannel & Bot"""
    __slots__ = ("channel", "_bot")

    def __init__(self, *, channel: discord.TextChannel, bot: discord.ext.commands.Bot):
        if not isinstance(channel, discord.TextChannel):
            raise InvalidContext
        if not isinstance(bot, discord.ext.commands.Bot):
            raise InvalidContext

        self.channel = channel
        self._bot = bot

    @property
    def bot(self) -> discord.ext.commands.Bot:
        return self._bot

    async def exit(self, message: str) -> None:
        await self.channel.send(message)
        raise ManagedCommandError
