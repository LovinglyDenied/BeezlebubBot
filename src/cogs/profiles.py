import asyncio
import logging

from typing import Optional
from datetime import datetime, timedelta

import discord
from discord.commands import slash_command, Option

from utils import mention_to_id
from database.player import Player, PlayerNotRegisterd
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

        embed=discord.Embed(
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
        user, discord_account = await self.get_user(player, ctx) or (None, None)
        if user is None or discord_account is None: return

        if user.last_active == datetime.min:
            last_active = None
        else:
            last_active = user.last_active.strftime(self.bot.date_format)

        owner = None

        embed: discord.Embed = self.create_profile_embed(
                discord_name = discord_account.name,
                join_date = user.join_date.strftime(self.bot.date_format),
                last_active = last_active,
                chaster_name = user.chaster_name,
                owner = owner,
                kinks_message = user.kinks_message,
                limits_message = user.limits_message,
                avatar = str(discord_account.display_avatar),
                derlict = (datetime.utcnow() - user.last_active > self.bot.derlict_time)
                )
        await ctx.respond(embed = embed)

    @slash_command(
            name="block",
            description="block the user")
    async def block(self,
            ctx: discord.ApplicationContext,
            player: Option(
                input_type = discord.User,
                name = "user",
                description = "the user to block"
                )
            ):
        user_id = mention_to_id(player)
        try:
            Player.block(ctx.user.id, user_id)
            await ctx.respond(f"Blocked {player}", ephemeral=True)
        except KeyError:
            await ctx.respond(f"{player} was already blocked", ephemeral=True)

    @slash_command(
            name="unblock",
            description="unblock the user")
    async def unblock(self,
            ctx: discord.ApplicationContext,
            player: Option(
                input_type = discord.User,
                name = "user",
                description = "the user to unblock"
                )
            ):
        user_id = mention_to_id(player)
        try:
            Player.block(ctx.user.id, user_id, unblock = True)
            await ctx.respond(f"Unblocked {player}", ephemeral=True)
        except ValueError:
            await ctx.respond(f"{player} was never blocked", ephemeral=True)

    def cog_unload(self):
        logging.info("Cog Relations unloaded")

def setup(bot):
    bot.add_cog(Profiles(bot))
    logging.info("Cog Relations loaded")

