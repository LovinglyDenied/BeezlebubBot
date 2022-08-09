import asyncio
import logging

from typing import Optional

import discord
from discord.commands import slash_command, Option

from database.user import User
from models import Player
from .base import BaseCog

class Relations(BaseCog):
    def __init__(self, bot):
        self.bot = bot
    @slash_command(
            name="block",
            description="block the user")

    async def block(self,
            ctx: discord.ApplicationContext,
            action: Option(
                input_type=str,
                name="action",
                description="\"add\" to block, \"remove\" to unblock",
                choices=[
                    "add",
                    "remove",
                    "list"
                    ]
                ),
            player: Option(
                input_type = discord.User,
                name = "user",
                description = "the user to block"
                )
            ):
        player: Player = await Player.from_mention(player, ctx = ctx)

        if action == "add":
            try:
                User.block(ctx.user.id, player.discord.id)
                await ctx.respond(f"Blocked {player.discord.mention}", ephemeral=True)
            except ValueError:
                await ctx.respond(f"{player.discord.mention} was already blocked", ephemeral=True)

        elif action == "remove":
            try:
                User.block(ctx.user.id, player.discord.id, unblock = True)
                await ctx.respond(f"Unblocked {player.discord.mention}", ephemeral=True)
            except ValueError:
                await ctx.respond(f"{player.discord.mention} was never blocked", ephemeral=True)

        elif action == "list":
            names = []
            for blocked_id in player.db.blocked:
                blocked = self.bot.get_user(blocked_id)
                if blocked is None: 
                    names.append(f"User {blocked_id}")
                else:
                    names.append(blocked.mention)
            await ctx.respond(", ".join(names), ephemeral = True)

    def cog_unload(self):
        logging.info("Cog Relations unloaded")

def setup(bot):
    bot.add_cog(Relations(bot))
    logging.info("Cog Relations loaded")

