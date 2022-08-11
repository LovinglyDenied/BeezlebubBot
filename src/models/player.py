from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Union

import discord

from database.user import User, UserNotRegisterd
from utils.helpers import mention_to_id
from .context import ModelContext, ModelACTX
from .managed_error import ManagedCommandError


class InvalidScope(ValueError):
    """A player method was called that cannot be called with the scope it operates under."""
    pass


class Player:
    """A wrapper class for a BeezelbubBot user. 
    Contains discord, database, and future Chaster methods and commands"""

    def __init__(self, *, context: ModelContext):
        self.context = context

    async def get_dm(self) -> discord.DMChannel:
        """Returns the DM channel of the bot with this user.
        Creates it if it didn't jet excist.
        Raises InvalidScope if not run on instances with initialised discord"""
        if not hasattr(self, "discord"):
            raise InvalidScope
        return self.discord.dm_channel or await self.discord.create_dm()

    async def get_owner(self, **kwargs) -> Player:
        """retuns a Player instance of the owner of the current player,
        initialised with the regular from_db kwargs in the present context"""
        if not hasattr(self, "db"):
            raise InvalidScope
        # TODO Make sure this is a valid entry.
        return await self.__class__.from_db_user(
            user=self.db.controlled_by[0],
            context=self.context,
            **kwargs
        )

    def is_owned_by(self, player: Player) -> bool:
        """Whether the player specified by argument is owned by the player the method is called on
        raises InvalidScope if not run on instances with initialised db"""
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
        owner = await self.get_owner(get_discord=True)
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
        return datetime.utcnow() - self.db.last_active > self.context.bot.derlict_time

    @property
    def deleteable(self) -> bool:
        """whether the user is currently deletable
        raises InvalidScope if not run on instance with initialised db"""
        if not hasattr(self, "db"):
            raise InvalidScope
        return datetime.utcnow() - self.db.last_active > self.context.bot.user_delete_time

    @property
    def last_active_str(self) -> Optional[str]:
        """last active date as a string
        raises InvalidScope if not run on instance with initialised db"""
        if not hasattr(self, "db"):
            raise InvalidScope
        if self.db.last_active == datetime.min:
            return None
        return self.db.last_active.strftime(self.context.bot.date_format)

    @property
    def join_date_str(self) -> str:
        """join date as a string
        raises InvalidScope if not run on instance with initialised db"""
        if not hasattr(self, "db"):
            raise InvalidScope
        return self.db.join_date.strftime(self.context.bot.date_format)

    async def is_administrator(self) -> bool:
        """Whether the user is a bot administrator
        raises InvalidScope if not run on instance with initialised discord"""
        if not hasattr(self, "discord"):
            raise InvalidScope
        return await self.context.bot.is_owner(self.discord)

    @classmethod
    async def from_mention(
        cls,
        mention_string: str,
        *,
        context: ModelContext,
        **kwargs
    ) -> Player:
        """Create a new instance from a mention string
        responds to context and trows ManagedCommandError if not possible"""
        try:
            discord_id = mention_to_id(mention_string)
        except ValueError:
            await context.exit(
                f"{mention_string} is not recognised as a player. Are you sure you used either a mention or a discord user ID?"
            )
        return await cls._init(discord_id=discord_id, context=context, **kwargs)

    @classmethod
    async def from_db_user(
        cls,
        user: User,
        *,
        context: ModelContext,
        get_discord: bool = True,
        get_chaster: bool = False
    ) -> Player:
        """Initialises a player with regular kwargs from a User object"""

        instance = cls(context=context)
        instance.db: User = user

        if get_discord:
            instance.discord: Union[discord.User, discord.Member] = await instance._get_discord(instance.db.discord_id)

        return instance

    @classmethod
    async def from_ctx(
        cls,
        ctx: discord.ApplicationContext,
        *,
        get_db: bool = False,
        get_chaster: bool = False
    ) -> Player:
        """Initialises a player with regular kwargs for the player who excecuted the command"""
        instance = cls(context=ModelACTX(ctx))
        instance.discord = ctx.user

        if get_db:
            instance.db: User = await instance._get_db(discord_id=ctx.user.id)

        return instance

    @classmethod
    async def _init(
        cls,
        *,
        discord_id: Optional[int] = None,
        db_id: Optional[int] = None,
        context: ModelContext,
        get_discord: bool = True,
        get_db: bool = False,
        get_chaster: bool = False,
        as_user: Optional[int] = None
    ) -> Player:
        """Initialises with the given flags, from the given data.
        It needs a discord_id or db_id to initialise any components
        raises ValueError if called with incorrect options.
        responds to context and trows ManagedCommandError for "runtime" errors"""

        if get_discord == False and get_db == False:
            raise ValueError("Cannot init player without either db or discord")

        instance = cls(context=context)

        # Use the discord_id from the database if None provided
        if discord_id is None and get_discord == True:
            get_db = True

        if get_db == True or as_user is not None:
            instance.db: User = await instance._get_db(discord_id=discord_id, db_id=db_id, as_user=as_user)

        if get_discord:
            instance.discord: Union[discord.User, discord.Member] = await instance._get_discord(discord_id or instance.db.discord_id)

        return instance

    async def _get_discord(self, discord_id: int) -> Union[discord.User, discord.Member]:
        """gets the discord instance of the player, or returns excisting one.
        responds to context and trows ManagedCommandError if not possible"""
        if hasattr(self, "discord"):
            return self.discord

        discord: Union[discord.Member,
                       discord.User] = self.context.bot.get_user(int(discord_id))

        if discord is None:
            try:
                await self.context.bot.fetch_user(int(discord_id))
                self.fetched = True
            except discord.NotFound:
                await self.context.exit(f"Could not find a user of the ID {discord_id}")

        return discord

    async def _get_db(
        self,
        *,
        discord_id: Optional[int] = None,
        db_id: Optional[int] = None,
        as_user: Optional[int] = None
    ) -> User:
        """Gets the db instance of the player, or returns excisting one.
        responds to context and trows ManagedCommandError if not possible"""
        if hasattr(self, "db") and as_user is None:
            return self.db

        try:
            db = User.get_user(discord_id=discord_id,
                               db_id=db_id, as_user=as_user)
        except UserNotRegisterd:
            await self.context.exit(f"No data found for {self.discord.mention}")

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
