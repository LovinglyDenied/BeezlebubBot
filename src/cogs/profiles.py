import asyncio
import logging

from typing import Optional

import discord
from discord.commands import slash_command, Option

from models import Player, ModelACTX, ModelNoneCTX, UnmanagedCommandError
from resources import create_profile_embed
from .base import BaseCog


class Profiles(BaseCog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(
        name="profile",
        description="shows the profile of the specified user")
    async def profile(
            self,
            ctx: discord.ApplicationContext,
            player: Option(
                input_type=discord.User,
                name="player",
                description="The user to get the profile from"
            )
    ):
        player: Player = await Player.from_mention(
            player,
            get_discord=True,
            get_db=True,
            context=ModelACTX(ctx)
        )
        try:
            owner: Optional[str] = await player.mention_owner(
                context=ModelNoneCTX(bot=self.bot))
        except UnmanagedCommandError:
            owner = "Owner could not be resolved."

        embed: discord.Embed = create_profile_embed(
            discord_name=player.discord.name,
            join_date=player.join_date_str,
            last_active=player.last_active_str,
            chaster_name=player.db.chaster_name,
            owner=owner,
            kinks_message=player.db.kinks_message,
            limits_message=player.db.limits_message,
            avatar=str(player.discord.display_avatar),
            derelict=player.derelict
        )
        await ctx.respond(embed=embed)

    def cog_unload(self):
        logging.info("Cog Profiles unloaded")


def setup(bot):
    bot.add_cog(Profiles(bot))
    logging.info("Cog Profiles loaded")
