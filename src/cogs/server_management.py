import asyncio
import logging

import discord
from discord import Permissions
from discord.ext import commands
from discord.commands import SlashCommandGroup, Option

from database.server import ServerSettings
from models import MainTextChannel, ModelACTX, ModelCCTX, create_main_text_channel
from .base import BaseCog


class ServerManager(BaseCog):
    server = SlashCommandGroup(
        "server",
        "Server administrator commands",
        default_member_permissions=Permissions(administrator=True),
        guild_only=True
    )
    welcome = server.create_subgroup(
        "welcome",
        "Welcome message settings",
        default_member_permissions=Permissions(administrator=True),
        guild_only=True
    )

    def __init__(self, bot):
        self.bot = bot

    @server.command(
        name="settings",
        description="set the general settings for your server")
    async def settings(
            self,
            ctx: discord.ApplicationContext,
            setting: Option(
                input_type=str,
                name="setting",
                description="The setting you want to set",
                choices=[
                    "save_settings_on_leave",
                    "run_welcome_message"
                ]
            ),
            value: Option(bool)
    ):
        ServerSettings.change_setting(ctx.guild.id, str(setting), bool(value))
        await ctx.respond(f"changed `{setting}` to `{value}`", ephemeral=True)

    @welcome.command(
        name="channels",
        description="set the channels for your welcome messge."
    )
    async def welcome_channels(
            self,
            ctx: discord.ApplicationContext,
            channel_type: Option(
                input_type=str,
                name="type",
                description="The type of channel you want to change",
                choices=[
                    "main",
                    "rules_button",
                    "roles_button",
                    "guide_button"
                ]
            ),
            channel_mention: Option(
                input_type=discord.channel,
                name="channel",
                description="The channel you want to use"
            )
    ):
        setting_name = f"{channel_type}_channel"
        channel = await MainTextChannel.from_mention(channel_mention, context=ModelACTX(ctx))
        ServerSettings.change_setting(ctx.guild.id, setting_name, int(
            channel.discord.id), group="welcome")
        await ctx.respond(
            f"changed the `{channel_type}` channel to {channel.discord.mention}",
            ephemeral=True
        )

    @welcome.command(
        name="text",
        description="set the text for your welcome messages")
    async def welcome_text(
            self,
            ctx: discord.ApplicationContext,
            setting: Option(
                input_type=str,
                name="setting",
                description="The setting you want to set",
                choices=[
                    "header",
                    "rules_button",
                    "roles_button",
                    "guide_button"
                ]
            ),
            text: Option(str)
    ):
        setting_name = f"{setting}_text"
        ServerSettings.change_setting(
            ctx.guild.id, setting_name, str(text), group="welcome")
        await ctx.respond(f"changed `{setting}` text to `{text}`", ephemeral=True)

    @server.command(
        name="dump",
        description="Dumps the database entry of your server in chat")
    async def dump(
        self,
            ctx: discord.ApplicationContext
    ):
        await ctx.respond(
            str(ServerSettings.query.find(
                {"server_id": ctx.guild.id}).first()),
            ephemeral=True
        )

    @staticmethod
    def create_welcome_embed(
            title: str,
            member_join: str,
            member_avatar: str,
            member_name: str
    ) -> discord.Embed:

        embed = discord.Embed(
            title=title,
            description=member_name,
            colour=0xA343CB
        )
        embed.add_field(
            name="**Joined Discord: **",
            value=member_join,
            inline=False
        )
        embed.set_thumbnail(url=member_avatar)

        return embed

    # This has to be done with a function instead of by subclassing View
    # The @button declarator does not support links
    @staticmethod
    def create_welcome_view(
            rules_link: str,
            rules_message: str,
            roles_link: str,
            roles_message: str,
            guide_link: str,
            guide_message: str,
    ) -> discord.ui.View:

        rules_button: discord.ui.Button = discord.ui.Button(
            label=rules_message,
            style=discord.ButtonStyle.link,
            url=rules_link
        )

        roles_button: discord.ui.Button = discord.ui.Button(
            label=roles_message,
            style=discord.ButtonStyle.link,
            url=roles_link
        )
        guide_button: discord.ui.Button = discord.ui.Button(
            label=guide_message,
            style=discord.ButtonStyle.link,
            url=guide_link
        )

        return discord.ui.View(rules_button, roles_button, guide_button)

    async def run_welcome_message(self, settings: ServerSettings, member: discord.Member):
        init_context = ModelCCTX(
            channel=member.guild.system_channel, bot=self.bot)
        channel = await create_main_text_channel(
            discord_id=settings.welcome.main_channel,
            context=init_context)

        if channel.discord.guild.id != member.guild.id:
            init_context.exit(
                f"Cannot send welcome message in {channel}, as it is not in the same guild.")

        main_context = ModelCCTX(channel=channel.discord, bot=self.bot)

        rules_channel = await create_main_text_channel(
            discord_id=settings.welcome.rules_button_channel,
            context=main_context)
        roles_channel = await create_main_text_channel(
            discord_id=settings.welcome.roles_button_channel,
            context=main_context)
        guide_channel = await create_main_text_channel(
            discord_id=settings.welcome.guide_button_channel,
            context=main_context)

        embed: discord.Embed = self.create_welcome_embed(
            title=settings.welcome.header_text,
            member_join=member.created_at.strftime(self.bot.date_format),
            member_avatar=str(member.display_avatar),
            member_name=str(member.mention)
        )
        view: discord.ui.View = self.create_welcome_view(
            rules_link=rules_channel.discord.jump_url,
            rules_message=settings.welcome.rules_button_text,
            roles_link=roles_channel.discord.jump_url,
            roles_message=settings.welcome.roles_button_text,
            guide_link=guide_channel.discord.jump_url,
            guide_message=settings.welcome.guide_button_text
        )
        await channel.discord.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot is True:
            return
        settings = ServerSettings.query.find(
            {"server_id": member.guild.id}).first()
        if settings.run_welcome_message:
            await self.run_welcome_message(settings, member)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        ServerSettings.enter_server(
            guild.id,
            channel_id=guild.system_channel.id,
            welcome_message=f"Welcome to {guild.name}!"
        )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        ServerSettings.leave_server(guild.id)

    def cog_unload(self):
        logging.info("Cog Server Management Unloaded")


def setup(bot):
    bot.add_cog(ServerManager(bot))
    logging.info("Cog Server Management loaded")
