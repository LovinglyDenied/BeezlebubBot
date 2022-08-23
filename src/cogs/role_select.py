import asyncio
import logging

import discord
from discord import RawReactionActionEvent, Permissions
from discord.ext import commands
from discord.commands import SlashCommandGroup, Option

from database.server import ServerSettings
from models import MainTextChannel, ModelACTX
from utils import MessageChannel
from .base import BaseCog


class ReactionRoles(BaseCog):
    roles = SlashCommandGroup(
        "roles",
        "configuration of role-select",
        default_member_permissions=Permissions(administrator=True),
        guild_only=True
    )

    def __init__(self, bot):
        self.bot = bot
        self.special_roles = {
            "❤️": "she/her",
            "💜": "they/them",
            "💙": "he/him",
            "💚": "safe"
        }

    @roles.command(
        name="channel",
        description="set the channel for role-select")
    async def channel(
            self,
            ctx: discord.ApplicationContext,
            channel_mention: Option(
                input_type=discord.channel,
                name="channel",
                description="The channel you want to use"
            )
    ):
        channel = await MainTextChannel.from_mention(channel_mention, context=ModelACTX(ctx))
        ServerSettings.change_setting(
            ctx.guild.id, "role_channel", int(channel.discord.id))
        await ctx.respond(f"The role channel has been changed to {channel.discord.mention}", ephemeral=True)

    async def add_role_from_payload(self, *, payload: RawReactionActionEvent, role: discord.Role, channel: MessageChannel):
        try:
            if role in payload.member.roles:
                await payload.member.remove_roles(role)
            elif payload.member is not None:
                await payload.member.add_roles(role)
        except discord.Forbidden:
            from resources import create_error_embed
            embed: discord.Embed = create_error_embed(
                """**Could not add specified role, no permission.**
                    The BeezlebubBot role has to be higher than the role you want the bot to add.""")
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                pass

    async def remove_reaction(self, *, payload: RawReactionActionEvent, channel: MessageChannel):
        messages = await channel.history(limit=10).flatten()
        message: discord.Message = discord.utils.get(
            messages, id=payload.message_id
        )

        if not any([r.me for r in message.reactions if r.emoji == payload.emoji]):
            await message.add_reaction(payload.emoji)
        await message.remove_reaction(payload.emoji, payload.member)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        try:
            role_name: str = self.special_roles[payload.emoji.name]
        except KeyError:
            role_name: str = payload.emoji.name

        guild: discord.Guild = discord.utils.get(
            self.bot.guilds, id=payload.guild_id)
        role: discord.Role = discord.utils.get(guild.roles, name=role_name)
        if role is None:
            return

        settings = ServerSettings.query.find(
            {"server_id": payload.guild_id}).first()
        if str(payload.channel_id) != str(settings.role_channel):
            return

        channel: MessageChannel = discord.utils.get(
            guild.channels, id=payload.channel_id
        )

        await self.add_role_from_payload(payload=payload, role=role, channel=channel)
        await self.remove_reaction(payload=payload, channel=channel)

    def cog_unload(self):
        logging.info("Cog Role Select unloaded")


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
    logging.info("Cog Role Select loaded")
