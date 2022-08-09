import os
import asyncio
import logging
import logging.handlers

from typing import List
from datetime import timedelta

import discord
from discord.ext import commands

from database import connect
from cogs import extensions


class BeezlebubBot(commands.Bot):
    def __init__(
        self,
        *args,
        extensions: List[str],
        datastore: str,
        date_format: str,
        derlict_time: timedelta,
        user_delete_time: timedelta,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.init_extensions = extensions
        self.datastore = datastore
        self.date_format = date_format
        self.derlict_time = derlict_time
        self.user_delete_time = user_delete_time

        self.setup_hook()

    def setup_hook(self):
        logging.info("=== Starting ===")

        # Establish database connection
        self.database_manager = connect.DBManager(uri = self.datastore)

        # Load bot management first, and without posibility of unload
        self.load_extensions("cogs.bot_management", store = False)
        
        # Load all other extensions
        for extension in self.init_extensions:
            self.load_extensions(extension, store=False)

def logger_setup():
    logger = logging.getLogger("discord")
    logger.setLevel(logging.INFO)

    handler = logging.handlers.RotatingFileHandler(
        filename = "logs.log",
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
    # from dotenv import load_dotenv
    # load_dotenv()

    logger_setup()

    intents = discord.Intents(
        members=True,
        messages=True,
        reactions=True,
        guilds=True
    )

    datastore = os.getenv("DATATOKEN")
    
    date_format = "%d %b %Y"
    derlict_time = timedelta(days=10)
    user_delete_time = timedelta(days=93)

    bot = BeezlebubBot(
        commands.when_mentioned_or('!'),
        extensions = extensions,
        intents = intents,
        datastore = datastore,
        date_format = date_format,
        derlict_time = derlict_time,
        user_delete_time = user_delete_time
    )
    bot.run(os.getenv("BOTTOKEN"))

if __name__ == "__main__":
    main()
