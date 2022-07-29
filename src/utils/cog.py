import asyncio
import logging

import discord
from discord.ext import commands

from database.player import Player

class BaseCog(commands.Cog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def cog_command_error(self, 
            ctx: discord.ApplicationContext, 
            error: Exception
            ):
        logging.warning(error)
        await ctx.respond(
                f"An error appeared while processing the command.```{error}```",
                ephemeral=True
                )

    async def cog_before_invoke(self, 
            ctx: discord.ApplicationContext 
            ):
        Player.update(ctx.user.id)

