import asyncio
import logging

import discord
from discord.commands import slash_command, Option

from utils import BaseCog
from database.player import Player, PlayerAlreadyRegisterd, PlayerNotRegisterd

class Profiles(BaseCog):
    def __init__(self, bot):
        self.bot = bot

    def create_profile_embed(
            member_name:str,
            member_join:str, 
            member_avatar:str 
            ) -> discord.Embed:

        embed=discord.Embed(
            title       = member_name,
            colour      = 0xA343CB
        )
        embed.add_field(
                name    = '**Joined BeezlebubBot: **', 
                value   = f'``'+member_join+f'``', 
                inline  = False
        )
        embed.set_thumbnail(url=member_avatar)

        return embed

    @slash_command(
            name="profile",
            description="shows the profile of the specified user")
    async def profile(self,
            ctx: discord.ApplicationContext,
            user: Option(
                input_type = discord.User,
                name = "user",
                description = "The user to get the profile from"
                )
            ):
        #Discord returns the "mention string," useless outside of Discord itself. 
        user_id = int(user.strip("<>@!"))
        profile = Player.querry.find({"ciscord_id": user_id}).first()
    
    @slash_command(
            name="block",
            description="block the user")
    async def block(self,
            ctx: discord.ApplicationContext,
            user: Option(
                input_type = discord.User,
                name = "user",
                description = "the user to block"
                )
            ):
        # Discord returns the "mention string," useless outside of Discord itself. 
        user_id = int(user.strip("<>@!"))
        #Player.block(ctx.user.id, user.id)
        Player["blocked"].append(user_id)
        await ctx.respond(f"Blocked {user}", ephemeral=True)

    def cog_unload(self):
        logging.info("Cog Relations unloaded")

def setup(bot):
    bot.add_cog(Profiles(bot))
    logging.info("Cog Relations loaded")

