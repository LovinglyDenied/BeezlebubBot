import asyncio
import logging

import discord
from discord.commands import SlashCommandGroup, Option

from database.user import User
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
        player: Player = await Player.from_mention(player, context=ModelACTX(ctx))
        try:
            User.block(ctx.user.id, player.discord.id)
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
        player: Player = await Player.from_mention(player, context=ModelACTX(ctx))
        try:
            User.block(ctx.user.id, player.discord.id, unblock=True)
            await ctx.respond(f"Unblocked {player.discord}", ephemeral=True)
        except ValueError:
            await ctx.respond(f"{player.discord} was never blocked", ephemeral=True)

    @block.command(
        name="list",
        description="list who you have blocked")
    async def list(
        self,
        ctx: discord.ApplicationContext
    ):
        player: Player = await Player.from_ctx(ctx, get_db=True)
        names = []
        for blocked_id in player.db.blocked:
            blocked = self.bot.get_user(blocked_id)
            if blocked is None:
                names.append(f"User {blocked_id}")
            else:
                names.append(str(blocked))
        if names == []:
            await ctx.respond("You don't have anyone blocked", ephemeral=True)
        else:
            await ctx.respond(", ".join(names), ephemeral=True)

    def cog_unload(self):
        logging.info("Cog Blocking unloaded")


def setup(bot):
    bot.add_cog(Blocking(bot))
    logging.info("Cog Blocking loaded")
