import os
import asyncio
import platform
import logging
import logging.handlers

from typing import Optional, List

import discord
from discord import ExtensionAlreadyLoaded, ExtensionNotLoaded
from discord import default_permissions
from discord.ext import commands
from discord.commands import slash_command, Option

from database import connect

extensions = [
        ]


class BeezlebubBot(commands.Bot):
    def __init__ (
            self,
            *args,
            extensions: List[str],
            datastore: str,
            **kwargs,
        ):
        super().__init__(*args, **kwargs)
        self.init_extensions = extensions
        self.datastore = datastore

        self.setup_hook()

    def setup_hook(self):
        logging.info("=== Starting ===")

        #Establish database connection
        connect.initialise(self.datastore)

        #Load extensions
        self.add_cog(CogManagement(self))

        for extension in self.init_extensions:
            self.load_extensions(extension, store = False)

    async def on_ready(self):
        logging.info(f'Discord.py API version: {discord.__version__}')
        logging.info(f'Python version: {platform.python_version()}')
        await self.set_status()
        logging.info(f'Logged in as {self.user} | {self.user.id}')

    async def set_status(self):
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"over you"
            )
        )

class CogManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(
            name = "cog",
            description = "manage the cogs of the bot")
    @default_permissions(administrator=True)
    async def manage_cogs(self,
            ctx: discord.ApplicationContext,
                action: Option(
                    input_type = str,
                    name = "action",
                    description = "The action you want to take",
                    choices = [
                        "load",
                        "unload",
                        "reload"
                        ]
                    ),
                extension: Option(
                    input_type = str,
                    name = "extension",
                    description = "The cog to change",
                    choices = extensions + ["all"]
                    )
                ):
        if extension == "all": 
            to_update = extensions
        else:
            to_update = [extension]

        for item in to_update:
            if action == "load": self.bot.load_extension(item)
            if action == "unload": self.bot.unload_extension(item)
            if action == "reload": self.bot.reload_extension(item)

        await ctx.respond(f"{to_update} got {action}ed") 
    

def logger_setup():
    logger = logging.getLogger("BeezlebubBot")
    logger.setLevel(logging.INFO)

    handler = logging.handlers.RotatingFileHandler(
            filename = "beezlebub.log",
            encoding = "utf-8",
            maxBytes = 32*1024*1024,
            backupCount = 5,
        )
    time_format = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(
            '[{asctime}] [{levelname:<8}] {name}: {message}', 
            time_format, 
            style='{'
        )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def main():
    logger_setup()

    intents = discord.Intents(
        members=True, 
        messages=True, 
        reactions=True,
        guilds=True
    )

    datastore = os.getenv("DATATOKEN")

    debug_guilds = [997821183057743872, 997992428743176243]

    bot =  BeezlebubBot(
            commands.when_mentioned_or('!'), 
            extensions = extensions, 
            intents = intents, 
            datastore = datastore,
            debug_guilds = debug_guilds)
    bot.run(os.getenv("BOTTOKEN"))

if __name__ == "__main__":
    main()

