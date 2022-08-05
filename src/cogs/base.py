import asyncio
import logging

from typing import Optional, Tuple, Union

import discord
from discord.ext import commands

from database.player import Player, PlayerNotRegisterd
from utils import mention_to_id

class BaseCog(commands.Cog):
    """The base cog all other cogs should inherit from
    Features:
    - Error handeling last resort (replies with the error if something goes wrong)
    - Registering the player or updating their last_active when a slash command is used"""
    # TODO: Write a function that allows the lookup of ids from mention, returning a proper error if faulty

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_user(self, 
            user_mention: str, 
            ctx: discord.ApplicationContext,
            *,
            as_user: Optional[int] = None
            ) -> Optional[Tuple[Player, Union[discord.Member, discord.User]]]:

        try:
            user_id = mention_to_id(user_mention)
        except ValueError:
            await ctx.respond(f"{user_mention} is not recognised as a player. Are you sure you used either a mention or a discord user ID?", ephemeral=True)
            return

        try:
            user = Player.get_user(user_id, as_user = as_user)
        except PlayerNotRegisterd:
            await ctx.respond(f"No data found for {user_mention}", ephemeral=True)
            return

        discord_account = ctx.bot.get_user(user_id)
        if discord_account is None:
            await ctx.respond(f"Could not find the discord account of {user_mention}", ephemeral=True)
            return

        return user, discord_account

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
