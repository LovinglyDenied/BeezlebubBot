from __future__ import annotations

from typing import Protocol, Union

import discord
from beartype import beartype

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
    def __init__(self, *, channel: Union[discord.TextChannel,discord.DMChannel], bot: discord.ext.commands.Bot):
        self.channel = channel
        self._bot = bot

    @property
    @beartype
    def bot(self) -> discord.ext.commands.Bot:
        return self._bot

    @beartype
    async def exit(self, message: str) -> None:
        await self.channel.send(message)
        raise ManagedCommandError
