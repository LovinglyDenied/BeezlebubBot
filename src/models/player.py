from __future__ import annotations

import asyncio
from datetime import datetime

import discord
from beartype import beartype
from beartype.typing import List, Coroutine, Optional
from bson.objectid import ObjectId

from database.user import DBUser, UserNotRegisterd
from utils import mention_to_id, get_player_name, DiscordMember
from .context_errors import ManagedCommandError, UnmanagedCommandError
from .context import ModelContext, ModelACTX, ModelNoneCTX


class InvalidScope(ValueError):
    """A player method was called that cannot be called with the scope it operates under."""
    pass


class Player:
    """A wrapper class for a BeezelbubBot user. 
    Contains discord, database, and future Chaster methods and commands"""

    @beartype
    def __init__(self, *, context: ModelContext):
        self.context = context

    @beartype
    async def get_dm(self) -> discord.DMChannel:
        """Returns the DM channel of the bot with this user.
        Creates it if it didn't jet excist.
        Raises InvalidScope if not run on instances with initialised discord.
        Does not guarantee the DM can actually be send."""
        if not hasattr(self, "discord"):
            raise InvalidScope
        return self.discord.dm_channel or await self.discord.create_dm()

    @beartype
    async def notify(self, message: str):
        """Tries to send a Notification DM to the user.
        Fails quietly if not able to."""
        from resources import create_notification_embed
        channel = await self.get_dm()
        embed = create_notification_embed(message)
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

    async def update_owner(self) -> Optional[Player]:
        """Updates the owner if derelict or missing.
        returns the owner after the operation, or none if the player doesn't have an owner after it"""
        try:
            owner = await self.get_owner(
                get_discord=False,
                get_chaster=False,
                context=ModelNoneCTX.from_other(self.context)
            )
        except UnmanagedCommandError:
            self._set_owner(self, trusts=False)
            return None

        try:
            await owner._get_discord(discord_id=owner.db.discord_id)
        except UnmanagedCommandError:
            pass

        if not self.has_owner:
            return None
        elif owner.derelict:
            self._set_owner(self, trusts=False)
            if hasattr(owner, "discord"):
                await owner.notify(
                    f"{self.discord.mention} is no longer owned by you because you went derelict")
            return None
        else:
            return owner

    @beartype
    async def get_owner(self, *, context: Optional[ModelContext] = None, **kwargs) -> Player:
        """retuns a Player instance of the owner of the current player,
        initialised with the regular init kwargs in the present context
        Updates the owner to self if owner was derelict."""
        if not hasattr(self, "db"):
            raise InvalidScope

        if context is None:
            context = self.context

        return await self.__class__._init(
            db_id=self.db.controller,
            context=context,
            get_db=True,
            **kwargs
        )

    @beartype
    async def set_owner(self, player: Player, *, trusts: bool):
        """Sets the player's owner to the one specified if able to."""
        if not hasattr(self, "discord") or not hasattr(player, "discord"):
            raise InvalidScope
        await self.update_owner()

        if self == player:
            await self.context.exit(
                "Cannot set owner to self")
        if self.is_owned_by(player):
            await self.context.exit(
                "Cannot set new owner, already owned by this player")
        if self.has_owner:
            await self.context.exit(
                "Cannot set owner, new target already has one.")

        self._set_owner(player, trusts=trusts)

        await self.notify(f"Your owner is now {player.discord.mention}.")
        await player.notify(f"You now own {self.discord.mention}.")

    @beartype
    async def free_all_owned(self):
        if not hasattr(self, "discord"):
            raise InvalidScope
        owned: Optional[List[Player]] = await self.get_owned()

        if owned is None:
            return

        for owned_player in owned:
            owned_player._set_owner(owned_player, trusts=False)
            owned_player.context = ModelNoneCTX.from_other(
                owned_player.context)

            try:
                owned_player.discord = await owned_player._get_discord(owned_player.db.discord_id)
                await owned_player.notify(f"You are no longer owned by {self.discord.mention}.")
            except ManagedCommandError:
                pass

    @beartype
    def _set_owner(self, player: Player, *, trusts: bool):
        if not hasattr(self, "db") or not hasattr(player, "db"):
            raise InvalidScope
        DBUser.set_controller(
            self.db._id, new_owner_id=player.db._id, trusts=trusts)

    @beartype
    def is_owned_by(self, player: Player) -> bool:
        """Whether the player specified by argument is owned by the player the method is called on
        raises InvalidScope if not run on instances with initialised db"""
        if not hasattr(self, "db") or not hasattr(player, "db"):
            raise InvalidScope
        return player.db._id == self.db.controller

    @beartype
    def owns(self, player: Player) -> bool:
        """Whether the player specified by argument owns the player the method is called on
        raises InvalidScope if not run on instances with initialised db"""
        if not hasattr(self, "db") or not hasattr(player, "db"):
            raise InvalidScope
        return self.db._id == player.db.controller

    @property
    @beartype
    def has_owner(self) -> bool:
        """Whether the player has an owner
        raises InvalidScope if not run on instances with initialised db"""
        return not self.owns(self)

    @beartype
    async def mention_owner(self, context: Optional[ModelContext] = None) -> Optional[str]:
        """Returns mention string for player's owner"""
        owner = await self.get_owner(get_discord=True, context=context)
        if owner == self:
            return None
        else:
            return owner.discord.mention

    # Cannot be beartyped, "Player" object too nested.
    async def get_owned(self) -> Optional[List[Player]]:
        """Returns a list of all the players owned by this player,
        or None if there are none
        raises InvalidScope if not run on instances with initialised db"""
        if not hasattr(self, "db"):
            raise InvalidScope
        controlling: List[DBUser] = DBUser.get_owned(self.db._id)

        coroutines: List[Coroutine] = [Player.from_db_user(
            controlled, context=self.context) for controlled in controlling]
        owned_all: List[Player] = await asyncio.gather(*coroutines)
        owned = [player for player in owned_all if player != self]

        if owned == []:
            return None
        else:
            return owned

    @property
    @beartype
    def derelict(self) -> bool:
        """whether the user is currently derelict
        raises InvalidScope if not run on instance with initialised db"""
        if not hasattr(self, "db"):
            raise InvalidScope
        return datetime.utcnow() - self.db.last_active > self.context.bot.derelict_time

    @property
    @beartype
    def deleteable(self) -> bool:
        """whether the user is currently deletable
        raises InvalidScope if not run on instance with initialised db"""
        if not hasattr(self, "db"):
            raise InvalidScope
        return datetime.utcnow() - self.db.last_active > self.context.bot.user_delete_time

    @property
    @beartype
    def last_active_str(self) -> Optional[str]:
        """last active date as a string
        raises InvalidScope if not run on instance with initialised db"""
        if not hasattr(self, "db"):
            raise InvalidScope
        if self.db.last_active == datetime.min:
            return None
        return self.db.last_active.strftime(self.context.bot.date_format)

    @property
    @beartype
    def join_date_str(self) -> str:
        """join date as a string
        raises InvalidScope if not run on instance with initialised db"""
        if not hasattr(self, "db"):
            raise InvalidScope
        return self.db.join_date.strftime(self.context.bot.date_format)

    @beartype
    async def is_administrator(self) -> bool:
        """Whether the user is a bot administrator
        raises InvalidScope if not run on instance with initialised discord"""
        if not hasattr(self, "discord"):
            raise InvalidScope
        return await self.context.bot.is_owner(self.discord)

    @classmethod
    @beartype
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
    @beartype
    async def from_db_user(
        cls,
        user: DBUser,
        *,
        context: ModelContext,
        get_discord: bool = True,
        get_chaster: bool = False
    ) -> Player:
        """Initialises a player with regular kwargs from a User object"""

        instance = cls(context=context)
        instance.db: DBUser = user

        if get_discord:
            instance.discord: DiscordMember = await instance._get_discord(instance.db.discord_id)

        return instance

    @classmethod
    @beartype
    async def from_ctx(
        cls,
        ctx: discord.ApplicationContext,
        *,
        get_db: bool = False,
        get_chaster: bool = False,
        as_user: Optional[int] = None
    ) -> Player:
        """Initialises a player with regular kwargs for the player who excecuted the command"""
        instance = cls(context=ModelACTX(ctx))
        instance.discord = ctx.user

        if get_db == True or as_user is not None:
            instance.db: DBUser = await instance._get_db(discord_id=ctx.user.id, as_user=as_user)

        return instance

    @classmethod
    @beartype
    async def _init(
        cls,
        *,
        discord_id: Optional[int] = None,
        db_id: Optional[ObjectId] = None,
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

        if db_id is None and discord_id is None:
            raise ValueError("Cannot init player without reference")

        instance = cls(context=context)

        if discord_id == instance.context.bot.application_id:
            await instance.context.exit("You cannot target the bot")

        # Use the discord_id from the database if None provided
        if discord_id is None and get_discord == True:
            get_db = True

        if get_db == True or as_user is not None:
            instance.db: DBUser = await instance._get_db(discord_id=discord_id, db_id=db_id, as_user=as_user)

        if get_discord:
            instance.discord: DiscordMember = await instance._get_discord(discord_id or instance.db.discord_id)

        return instance

    @beartype
    async def _get_discord(self, discord_id: int) -> DiscordMember:
        """gets the discord instance of the player, or returns excisting one.
        responds to context and trows ManagedCommandError if not possible"""
        if hasattr(self, "discord"):
            return self.discord

        if discord_id == self.context.bot.application_id:
            await self.context.exit("You cannot target the bot")

        member: Optional[DiscordMember] = self.context.bot.get_user(discord_id)
        if member is not None:
            return member

        try:
            member = await self.context.bot.fetch_user(discord_id)
            self.fetched = True
            return member
        except discord.NotFound:
            await self.context.exit(f"Could not find a user of the ID {discord_id}")

    @beartype
    async def _get_db(
        self,
        *,
        discord_id: Optional[int] = None,
        db_id: Optional[ObjectId] = None,
        as_user: Optional[int] = None
    ) -> DBUser:
        """Gets the db instance of the player, or returns excisting one.
        responds to context and trows ManagedCommandError if not possible"""
        if hasattr(self, "db") and as_user is None:
            return self.db

        try:
            db = DBUser.get_user(
                discord_id=discord_id,
                db_id=db_id,
                as_user=as_user
            )
        except UserNotRegisterd:
            if discord_id is not None:
                discord_name = await get_player_name(
                    discord_id, bot=self.context.bot)
                await self.context.exit(f"No data found for {discord_name}")
            elif db_id is not None:
                await self.context.exit(f"Database entry not found: {db_id}")
            else:
                raise ValueError  # DBUser.get_user should have already done this, but better safe than sorry

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


@beartype
async def create_player(*args, **kwargs) -> Player:
    return await Player._init(*args, **kwargs)
