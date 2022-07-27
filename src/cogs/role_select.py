import asyncio
import logging

import discord
from discord import guild_only, default_permissions, RawReactionActionEvent
from discord.ext import commands
from discord.commands import slash_command, Option

from database.server import ServerSettings

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.special_roles = {
                "❤️": "she/her",
                "💜": "they/them",
                "💙": "he/him",
                "💚": "safe"
                }

    @slash_command(
            name="role_channel", 
            description="set the role-select ")
    @guild_only()
    @default_permissions(administrator=True)
    async def role_channel(self, 
            ctx: discord.ApplicationContext,
            channel: Option(str)
            ):
        ServerSettings.change_setting(ctx.guild.id, "role_channel", channel)
        await ctx.respond(f"The role channel has been changed to {channel}", ephemeral=True)


    async def add_role_from_payload(self, payload: RawReactionActionEvent, role: discord.Role):
        if role in payload.member.roles:
            await payload.member.remove_roles(role)
        elif payload.member is not None:
            await payload.member.add_roles(role)

    async def remove_reaction(self, payload: RawReactionActionEvent, guild: discord.Guild):   
        channel: discord.GuildChannel = discord.utils.get(guild.channels, id = payload.channel_id)
        messages = await  channel.history(limit = 10).flatten()
        message: discord.Message = discord.utils.get(messages, id = payload.message_id)

        if not any([r.me for r in message.reactions if r.emoji == payload.emoji]):
            await message.add_reaction(payload.emoji)
        await message.remove_reaction(payload.emoji, payload.member)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if payload.user_id == self.bot.user.id: return

        try:
            role_name:str = self.special_roles[payload.emoji.name]
        except KeyError:
            role_name:str = payload.emoji.name

        guild: discord.Guild = discord.utils.get(self.bot.guilds, id = payload.guild_id)
        role: discord.Role = discord.utils.get(guild.roles, name = role_name)
        if role is None: return

        settings = ServerSettings.query.find({"server_id": payload.guild_id}).first()
        if str(payload.channel_id) != str(settings.role_channel): return

        await self.add_role_from_payload(payload, role)
        await self.remove_reaction(payload, guild)

    def cog_unload(self):
        logging.info("Cog Role Select unloaded")

def setup(bot):
    bot.add_cog(ReactionRoles(bot))
    logging.info("Cog Role Select loaded")

