import asyncio
import logging

import discord
from discord.ext import commands
from discord.commands import slash_command


from utils import sched
from database.player import Player, PlayerAlreadyRegisterd, PlayerNotRegisterd
from .base import BaseCog

class PlayerManager(BaseCog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(
            name="register", 
            description="registers your user, if this was not done already")
    async def register(self,
            ctx: discord.ApplicationContext
            ):
        try:
            Player.register(ctx.user.id)
            await ctx.respond(f"Registered {ctx.user.mention}", ephemeral=True)
        except PlayerAlreadyRegisterd:
            await ctx.respond(f"Player {ctx.user.mention} was already registered", ephemeral=True)

    @slash_command(
            name="unregister", 
            description="unreregisters your user, if this was not done already")
    async def unregister(self,
            ctx: discord.ApplicationContext
            ):
        try:
            Player.unregister(ctx.user.id)
            await ctx.respond(f"unregistered {ctx.user.mention}", ephemeral=True)
        except PlayerNotRegisterd:
            await ctx.respond(f"Player {ctx.user.mention} was never registered", ephemeral=True)

    @slash_command(
            name="update", 
            description="does a simple update of your last active")
    async def update(self,
            ctx: discord.ApplicationContext
            ):
        Player.update(ctx.user.id)
        await ctx.respond(f"Updated {ctx.user.mention}'s Last active status", ephemeral=True)

    @slash_command(
            name="get_data", 
            description="Dumps your database entry in chat")
    async def get_data(self,
            ctx: discord.ApplicationContext
            ):
        try:
            await ctx.respond(Player.get_settings(ctx.user.id), ephemeral=True)
        except PlayerNotRegisterd:
            await ctx.respond(f"No data found for {ctx.user.mention}", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot: return
        Player.join(member.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.bot: return
        Player.leave(member.id, delete_time=self.bot.user_delete_time)

    @commands.Cog.listener()
    async def on_guild_join(self, guild:discord.Guild):
        for member in guild.members:
            if member.bot: continue 
            Player.join(member.id)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild:discord.Guild):
        for member in guild.members:
            if member.bot: continue 
            Player.leave(member.id, delete_time=self.bot.user_delete_time)

    @slash_command(
            name="update_data", 
            description="does an update of the database")
    async def update_data(self,
            ctx: discord.ApplicationContext
            ):
        from database.player import database_updater
        database_updater()
        await ctx.respond(f"Updated database", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        Player.init_updater(bot = self.bot)
        sched.add_job(
                "database:player.database_updater", 
                "cron", hour=2, 
                id = "update_database",
                replace_existing=True
                )

    #In this cog, commands should not call Player.update()
    #Therefore, BaseCog behaviour needs to be overwritten
    async def cog_before_invoke(self, 
            ctx: discord.ApplicationContext 
            ):
        pass

    def cog_unload(self):
        logging.info("Cog PlayerManagement unloaded")

def setup(bot):
    bot.add_cog(PlayerManager(bot))
    logging.info("Cog PlayerManagement loaded")

