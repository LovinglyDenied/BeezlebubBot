import asyncio
import logging

import discord
from discord import guild_only, default_permissions
from discord.ext import commands
from discord.commands import slash_command, Option

from database.server import ServerSettings
from .base import BaseCog

class ServerManager(BaseCog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(
            name="serversettings", 
            description="set the general settings for your server")
    @guild_only()
    @default_permissions(administrator=True)
    async def serversettings(self,
            ctx: discord.ApplicationContext,
            setting: Option(
                input_type = str,
                name = "setting",
                description = "The setting you want to set",
                choices = [
                    "save_settings_on_leave",
                    "run_welcome_message"
                    ]
                ),
            value: Option(bool)
            ):
        ServerSettings.change_setting(ctx.guild.id, setting, value)
        await ctx.respond(f"changed `{setting}` to `{value}`", ephemeral=True)

    @slash_command(
            name="welocomeettings", 
            description="set the welcome settings for your server")
    @guild_only()
    @default_permissions(administrator=True)
    async def welcomesettings(self,
            ctx: discord.ApplicationContext,
            setting: Option(
                input_type = str,
                name = "setting",
                description = "The setting you want to set",
                choices = [
                    "welcome_message",
                    "welcome_channel",
                    "rules_link",
                    "rules_message",
                    "roles_link",
                    "roles_message",
                    "guide_link",
                    "guide_message"
                    ]
                ),
            value: Option(str)
            ):
        ServerSettings.change_setting(ctx.guild.id, setting, value, group = "welcome")
        await ctx.respond(f"changed `welcome.{setting}` to `{value}`", ephemeral=True)

    @slash_command(
            name="get_settings", 
            description="Dumps the database entry of your server in chat")
    @guild_only()
    @default_permissions(administrator=True)
    async def get_settings(self,
            ctx: discord.ApplicationContext
            ):
        await ctx.respond(
            str(ServerSettings.query.find({"server_id": ctx.guild.id}).first()), 
            ephemeral=True
            )

    @staticmethod
    def create_welcome_embed(
            title:str, 
            member_join:str, 
            member_avatar:str, 
            member_name:str
            ) -> discord.Embed:

        embed=discord.Embed(
            title       = title,
            description = member_name,
            colour      = 0xA343CB
        )
        embed.add_field(
                name    = "**Joined Discord: **", 
                value   = member_join, 
                inline  = False
        )
        embed.set_thumbnail(url=member_avatar)

        return embed

    # This has to be done with a function instead of by subclassing View
    # The @button declarator does not support links
    @staticmethod
    def create_welcome_view(
            rules_link:str,
            rules_message:str,
            roles_link:str,
            roles_message:str,
            guide_link:str,
            guide_message:str,
            ) -> discord.ui.View:

        rules_button: discord.ui.Button = discord.ui.Button(
                label = rules_message,
                style = discord.ButtonStyle.link,
                url   = rules_link
                )

        roles_button: discord.ui.Button = discord.ui.Button(
                label = roles_message,
                style = discord.ButtonStyle.link,
                url   = roles_link
                )
        guide_button: discord.ui.Button = discord.ui.Button(
                label = guide_message,
                style = discord.ButtonStyle.link,
                url   = guide_link
                )

        return discord.ui.View(rules_button, roles_button, guide_button)


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot is True:
            return
        settings = ServerSettings.query.find({"server_id": member.guild.id}).first()
        if settings.run_welcome_message:
            channel = member.guild.get_channel(settings.welcome.welcome_channel)
            embed: discord.Embed  = self.create_welcome_embed(
                    title         = settings.welcome.welcome_message,
                    member_join   = member.created_at.strftime(self.bot.date_format),
                    member_avatar = str(member.display_avatar),
                    member_name   = str(member.mention)
                    )
            view: discord.ui.View = self.create_welcome_view(
                    rules_link    = settings.welcome.rules_link,
                    rules_message = settings.welcome.rules_message,
                    roles_link    = settings.welcome.roles_link,
                    roles_message = settings.welcome.roles_message,
                    guide_link    = settings.welcome.guide_link,
                    guide_message = settings.welcome.guide_message
                    )
            await channel.send(embed=embed, view=view)


    @commands.Cog.listener()
    async def on_guild_join(self, guild:discord.Guild):
        ServerSettings.enter_server(
                guild.id, 
                channel_id = guild.system_channel.id, 
                welcome_message = f"Welcome to {guild.name}!"
                )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild:discord.Guild):
        ServerSettings.leave_server(guild.id)

    def cog_unload(self):
        logging.info("Cog Server Management Unloaded")

def setup(bot):
    bot.add_cog(ServerManager(bot))
    logging.info("Cog Server Management loaded")
