import asyncio
import logging

import discord
from discord.ext import commands
from discord.commands import slash_command, Option

from cogs import extensions
from utils import BaseCog
from database.player import Player

class BotManager(BaseCog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(
        name="cog",
        description="manage the cogs of the bot")
    async def manage_cogs(self,
        ctx: discord.ApplicationContext,
        action: Option(
            input_type=str,
            name="action",
            description="The action you want to take",
            choices=[
                "load",
                "unload",
                "reload"
            ]
        ),
        extension: Option(
            input_type=str,
            name="extension",
            description="The cog to change",
            choices=extensions + ["all"]
        )
    ):
        if extension == "all":
            to_update = extensions
        else:
            to_update = [extension]

        for item in to_update:
            if action == "load":
                self.bot.load_extension(item)
            if action == "unload":
                self.bot.unload_extension(item)
            if action == "reload":
                self.bot.reload_extension(item)

        await ctx.respond(f"{to_update} got {action}ed", ephemeral=True)

    async def set_status(self):
        await self.bot.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"over you"
            )
        )

    @commands.Cog.listener()
    async def on_ready(self):
        await self.set_status()

    def cog_unload(self):
        logging.info("Cog Bot Management Unloaded")

def setup(bot):
    bot.add_cog(BotManager(bot))
    logging.info("Cog Bot Management loaded")
