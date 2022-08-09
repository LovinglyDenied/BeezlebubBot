import asyncio
import logging

from typing import Optional

import discord
from discord.commands import slash_command, Option

from models import Player
from .base import BaseCog

class Profiles(BaseCog):
    def __init__(self, bot):
        self.bot = bot

    def create_profile_embed(self,
            *,
            discord_name:str,
            join_date:str, 
            last_active: Optional[str],
            chaster_name: Optional[str],
            owner: Optional[str],
            kinks_message: str,
            limits_message: str,
            avatar:str,
            derlict:bool
            ) -> discord.Embed:

        embed = discord.Embed(
                title       = f"**{discord_name}**",
                colour      = 0xA343CB
                )
        embed.add_field(
                name    = "**First Appeared: **", 
                value   = join_date, 
                inline  = False
                )
        if last_active is not None:
            embed.add_field(
                    name = "**Last Active: **",
                    value = last_active,
                    inline = False
                    )
        if chaster_name is not None:
            embed.add_field(
                    name = "**Chaster Name: **",
                    value = chaster_name,
                    inline = False
                    )
        if owner is not None:
            embed.add_field(
                    name = "**Owner: **",
                    value = owner,
                    inline = False
                    )
        embed.add_field(
                name = "**Kinks Message: **",
                value = kinks_message,
                inline = False
                )
        embed.add_field(
                name = "**Limits Message: **",
                value = limits_message,
                inline = False
                )
        embed.set_thumbnail(url=avatar)
        if derlict:
            embed.set_footer(text = "Notice: this user is currently derlict.")

        return embed

    @slash_command(
            name="profile",
            description="shows the profile of the specified user")
    async def profile(self,
            ctx: discord.ApplicationContext,
            player: Option(
                input_type = discord.User,
                name = "player",
                description = "The user to get the profile from"
                )
            ):
        player: Player = await Player.from_mention(player, get_discord=True, get_db=True, ctx = ctx)
        owner: str = await player.mention_owner()

        embed: discord.Embed = self.create_profile_embed(
                discord_name = player.discord.name,
                join_date = player.join_date_str,
                last_active = player.last_active_str,
                chaster_name = player.db.chaster_name,
                owner = owner,
                kinks_message = player.db.kinks_message,
                limits_message = player.db.limits_message,
                avatar = str(player.discord.display_avatar),
                derlict = player.derlict
                )
        await ctx.respond(embed = embed)

    def cog_unload(self):
        logging.info("Cog Profiles unloaded")

def setup(bot):
    bot.add_cog(Profiles(bot))
    logging.info("Cog Profiles loaded")

