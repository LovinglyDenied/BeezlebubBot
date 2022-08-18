import asyncio
import logging

from typing import List, Coroutine

import discord
from discord.commands import SlashCommandGroup, Option

from database.user import DBUser
from utils import mention_to_id, get_player_name
from models import Player, ModelACTX
from .base import BaseCog


class Blocking(BaseCog):
    block = SlashCommandGroup("block", "Manage who you have blocked")

    def __init__(self, bot):
        self.bot = bot

    @block.command(
        name="add",
        description="block the user")
    async def add(
        self,
        ctx: discord.ApplicationContext,
        player: Option(
            input_type=discord.User,
            name="user",
            description="the user to block"
        )
    ):
        instantiator: Player = await Player.from_ctx(ctx)
        player: Player = await Player.from_mention(player, context=ModelACTX(ctx))
        if player == instantiator:
            await ctx.respond("You cannot block yourself, silly!", ephemeral=True)
            return
        try:
            DBUser.block(ctx.user.id, player.discord.id)
            await ctx.respond(f"Blocked {player.discord}", ephemeral=True)
        except ValueError:
            await ctx.respond(f"{player.discord} was already blocked", ephemeral=True)

    @block.command(
        name="remove",
        description="unblock the user")
    async def remove(
        self,
        ctx: discord.ApplicationContext,
        player: Option(
            input_type=discord.User,
            name="user",
            description="the user to block"
        )
    ):
        # Not using the Player model to allow for deletion of removed discord accounts
        player_id: int = mention_to_id(player)
        player_name: str = await get_player_name(player_id, bot=self.bot)
        try:
            DBUser.block(ctx.user.id, player_id, unblock=True)
            await ctx.respond(f"Unblocked {player_name}", ephemeral=True)
        except ValueError:
            await ctx.respond(f"{player_name} was never blocked", ephemeral=True)

    @block.command(
        name="list",
        description="list who you have blocked")
    async def list(
        self,
        ctx: discord.ApplicationContext
    ):
        player: Player = await Player.from_ctx(ctx, get_db=True)
        # Not using the Player model to allow for deletion of removed discord accounts
        coroutines: List[Coroutine] = [get_player_name(
            blocked_id, bot=self.bot) for blocked_id in player.db.blocked]
        names: List[str] = await asyncio.gather(*coroutines)
        if names == []:
            await ctx.respond("You don't have anyone blocked", ephemeral=True)
        else:
            entries = []
            for name, id in zip(names, player.db.blocked):
                entries.append(f"{name}, ID: {str(id)}")
            await ctx.respond("\n".join(entries), ephemeral=True)

    def cog_unload(self):
        logging.info("Cog Blocking unloaded")


def setup(bot):
    bot.add_cog(Blocking(bot))
    logging.info("Cog Blocking loaded")
