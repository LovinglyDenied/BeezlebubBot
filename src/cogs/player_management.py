import asyncio
import logging

import discord
from discord.ext import commands
from discord.commands import SlashCommandGroup

from utils import sched, scheduler_setup
from database.user import DBUser, UserAlreadyRegisterd, UserNotRegisterd
from models import Player, create_player, ModelNoneCTX
from .base import BaseCog


class PlayerManager(BaseCog):
    data = SlashCommandGroup("data", "Manage the data the bot has on you")

    def __init__(self, bot):
        self.bot = bot

    @data.command(
        name="register",
        description="registers your user, if this was not done already")
    async def register(
            self,
            ctx: discord.ApplicationContext
    ):
        try:
            DBUser.register(ctx.user.id)
            await ctx.respond(f"Registered {ctx.user.mention}", ephemeral=True)
        except UserAlreadyRegisterd:
            await ctx.respond(f"Player {ctx.user.mention} was already registered", ephemeral=True)

    @data.command(
        name="unregister",
        description="unreregisters your user and deletes all data, if this was not done already")
    async def unregister(
            self,
            ctx: discord.ApplicationContext
    ):
        # This going wrong should not prevent anyone from unregistering.
        try:
            player: Player = await create_player(
                discord_id=ctx.user.id, 
                get_db=True, 
                context=ModelNoneCTX(bot=self.bot)
            )
            await player.free_all_owned()
        except Exception:
            pass

        try:
            DBUser.unregister(discord_id=ctx.user.id)
            await ctx.respond(f"unregistered {ctx.user.mention}", ephemeral=True)
        except UserNotRegisterd:
            await ctx.respond(f"Player {ctx.user.mention} was never registered", ephemeral=True)

    @data.command(
        name="update",
        description="Updates your database entry")
    async def update(
            self,
            ctx: discord.ApplicationContext
    ):
        references = len(ctx.user.mutual_guilds)
        DBUser.update(ctx.user.id, ref_count=references)
        await ctx.respond(f"Updated {ctx.user.mention}'s database entry", ephemeral=True)

    @data.command(
        name="dump",
        description="Dumps your database entry in chat")
    async def get_data(
            self,
            ctx: discord.ApplicationContext
    ):
        try:
            await ctx.respond(DBUser.get_settings(ctx.user.id), ephemeral=True)
        except UserNotRegisterd:
            await ctx.respond(f"No data found for {ctx.user.mention}", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        DBUser.join(member.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.bot:
            return
        DBUser.leave(member.id, delete_time=self.bot.user_delete_time)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        for member in guild.members:
            if member.bot:
                continue
            DBUser.join(member.id)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        for member in guild.members:
            if member.bot:
                continue
            DBUser.leave(member.id, delete_time=self.bot.user_delete_time)

    @commands.Cog.listener()
    async def on_connect(self):
        DBUser.init_updater(bot=self.bot)

    @commands.Cog.listener()
    async def on_ready(self):
        scheduler_setup()
        sched.add_job(
            "database:user.database_updater",
            "cron", hour=2,
            id="update_database",
            replace_existing=True
        )

    # In this cog, commands should not call Player.update()
    # Therefore, BaseCog behaviour needs to be overwritten
    async def cog_before_invoke(
        self,
        ctx: discord.ApplicationContext
    ):
        pass

    def cog_unload(self):
        logging.info("Cog PlayerManagement unloaded")


def setup(bot):
    bot.add_cog(PlayerManager(bot))
    logging.info("Cog PlayerManagement loaded")
