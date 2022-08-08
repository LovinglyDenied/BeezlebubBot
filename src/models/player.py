from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Union

import discord

from database.user import User, UserNotRegisterd
from utils.helpers import mention_to_id

from .managed_error import ManagedCommandError


class InvalidScope(Exception):
    """A player method was called that cannot be called with the scope it operates under."""
    pass


class Player:
    """A wrapper class for a BeezelbubBot user. 
    Contains discord, database, and future Chaster methods and commands"""

    def __init__(self, *, ctx: discord.ApplicationContext):
        self.ctx = ctx

    async def get_owner(self, **kwargs) -> Player:
        if not hasattr(self, "db"):
            raise InvalidScope
        # TODO Make sure this is a valid entry.
        return await Player.from_db_user(
            user=self.db.controlled_by[0],
            ctx=self.ctx,
            **kwargs
        )

    def is_owned_by(self, player: Player) -> bool:
        """Whether the player specified by argument is owned by the player the method is called on
        raises InvalidScope if not run on instances with initialised db"""
        print(self, player)
        if not hasattr(self, "db") or not hasattr(player, "db"):
            raise InvalidScope
        return any([user._id == player.db._id for user in self.db.controlled_by])

    def owns(self, player: Player) -> bool:
        """Whether the player specified by argument owns the player the method is called on
        raises InvalidScope if not run on instances with initialised db"""
        if not hasattr(self, "db") or not hasattr(player, "db"):
            raise InvalidScope
        return any([user._id == player.db._id for user in self.db.controls])

    async def mention_owner(self) -> Optional[str]:
        """Returns mention string for player's owner"""
        owner = await self.get_owner(get_discord = True)
        if owner == self: 
            return None
        else:
            return owner.discord.mention

    @property
    def derlict(self) -> bool:
        """whether the user is currently derlict
        raises InvalidScope if not run on instance with initialised db"""
        if not hasattr(self, "db"):
            raise InvalidScope
        return datetime.utcnow() - self.db.last_active > self.ctx.bot.derlict_time

    @property
    def deleteable(self) -> bool:
        """whether the user is currently deletable
        raises InvalidScope if not run on instance with initialised db"""
        if not hasattr(self, "db"):
            raise InvalidScope
        return datetime.utcnow() - self.db.last_active > self.ctx.bot.user_delete_time

    @property
    def last_active_str(self) -> Optional[str]:
        """last active date as a string
        raises InvalidScope if not run on instance with initialised db"""
        if not hasattr(self, "db"):
            raise InvalidScope
        if self.db.last_active == datetime.min:
            return None
        return self.db.last_active.strftime(self.ctx.bot.date_format)

    @property
    def join_date_str(self) -> str:
        """join date as a string
        raises InvalidScope if not run on instance with initialised db"""
        if not hasattr(self, "db"):
            raise InvalidScope
        return self.db.join_date.strftime(self.ctx.bot.date_format)

    @classmethod
    async def from_mention(
        cls,
        mention_string: str,
        *,
        ctx: discord.ApplicationContext,
        **kwargs
    ) -> Player:
        """Create a new instance from a mention string
        responds to ctx and trows ManagedCommandError if not possible"""
        try:
            discord_id = mention_to_id(mention_string)
        except ValueError:
            await ctx.respond(f"{mention_string} is not recognised as a player. Are you sure you used either a mention or a discord user ID?", ephemeral=True)
            raise ManagedCommandError

        return await cls._init(discord_id=discord_id, ctx=ctx, **kwargs)

    @classmethod
    async def from_db_user(
        cls,
        user: User,
            *,
            ctx: discord.ApplicationContext,
            get_discord: bool = True,
            get_chaster: bool = False
    ) -> Player:

        instance = Player(ctx=ctx)
        instance.db = user

        if get_discord:
            instance.discord = await instance._get_discord(instance.db.discord_id)

        return instance

    @classmethod
    async def _init(
        cls,
        *,
        discord_id: Optional[int] = None,
        db_id: Optional[int] = None,
        ctx: discord.ApplicationContext,
        from_ctx: Optional[bool] = False,
        get_discord: bool = True,
        get_db: bool = False,
        get_chaster: bool = False,
        as_user: Optional[int] = None
    ) -> Player:
        """Initialises with the given flags, from the given data.
        If from_ctx is passed as false, it needs a discord_id or db_id to initialise any components
        raises ValueError if called with incorrect options.
        responds to ctx and trows ManagedCommandError for "runtime" errors"""
        instance = Player(ctx=ctx)

        # Use the discord_id from the database if None provided
        if discord_id is None and get_discord == True:
            get_db = True

        if from_ctx:
            if discord_id or db_id or get_discord:
                raise ValueError(
                    "Too many perameters given Player.discord is always initlaised via ctx, and an ID is not needed.")
            instance.discord = ctx.user
            discord_id = instance.discord.id

        if get_db == True or as_user is not None:
            instance.db = await instance._get_db(discord_id=discord_id, db_id=db_id, as_user=as_user)

        if get_discord:
            instance.discord = await instance._get_discord(discord_id or instance.db.discord_id)

        return instance

    async def _get_discord(self, discord_id: int) -> Union[discord.User, discord.Member]:
        """gets the discord instance of the player, or returns excisting one.
        responds to ctx and trows ManagedCommandError if not possible"""
        if hasattr(self, "discord"):
            return self.discord

        discord: Union[discord.Member,
                       discord.User] = self.ctx.bot.get_user(discord_id)
        if discord is None:  # Make sure assignment never happens if None
            self.ctx.respond(f"Could not find a user of the ID {discord_id}")
            raise ManagedCommandError

        return discord

    async def _get_db(
        self,
        *,
        discord_id: Optional[int] = None,
        db_id: Optional[int] = None,
        as_user: Optional[int] = None
    ) -> User:
        """Gets the db instance of the player, or returns excisting one.
        responds to ctx and trows ManagedCommandError if not possible"""
        if hasattr(self, "db") and as_user is None:
            return self.db

        try:
            db = User.get_user(discord_id=discord_id,
                               db_id=db_id, as_user=as_user)
        except UserNotRegisterd:
            await self.ctx.respond(f"No data found for {self.discord.mention}", ephemeral=True)
            raise ManagedCommandError

        return db

    def __eq__(self, other):
        if isinstance(other, Player):
            if hasattr(self, "db") and hasattr(other, "db"):
                return self.db._id == other.db._id
            else:
                self_id = self.discord.id or self.db.discord_id
                other_id = other.discord.id or other.db.discord_id
                return self_id == other_id
        else:
            return NotImplemented


async def create_player(*args, **kwargs) -> Player:
    return await Player._init(*args, **kwargs)
