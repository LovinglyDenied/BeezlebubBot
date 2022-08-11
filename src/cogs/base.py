import asyncio
import logging

import discord
from discord.ext import commands

from database.user import User
from models import ManagedCommandError


class BaseCog(commands.Cog):
    """The base cog all other cogs should inherit from
    Features:
    - Error handeling last resort (replies with the error if something goes wrong)
    - Registering the player or updating their last_active when a slash command is used"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def cog_command_error(
        self,
        ctx: discord.ApplicationContext,
        error: Exception
    ):
        if isinstance(error, ManagedCommandError):
            return

        logging.warning(error)
        await ctx.respond(
            f"An error appeared while processing the command.```{error}```",
            ephemeral=True
        )

    async def cog_before_invoke(
        self,
        ctx: discord.ApplicationContext
    ):
        User.update(ctx.user.id)
