from __future__ import annotations

from typing import Any, List, Optional
from datetime import datetime, timedelta, timezone

from ming import schema as s
from ming.odm import FieldProperty
from ming.odm.property import ForeignIdProperty, RelationProperty
from ming.odm.declarative import MappedClass
from ming.odm import Mapper
from bson.objectid import ObjectId

from utils import classproperty
from .connect import DBManager
from .tasks import TaskTags, Tasks


class UserAlreadyRegisterd(Exception):
    pass


class UserNotRegisterd(Exception):
    pass


class RefCountUpdater:
    """Callable used for the scheduler to be able to access the reference count updater."""

    def __init__(self, *, bot=None):
        self.bot = bot

    def __call__(self):
        user_ids = []
        for guild in self.bot.guilds:
            user_ids += [member.id for member in guild.members]
        DBUser.update_database(user_ids, delete_time=self.bot.user_delete_time)


class UserKinks(MappedClass):
    class __mongometa__:
        name = "user_kinks"
        session = DBManager.add_session(name)

    _id = FieldProperty(s.ObjectId)
    kink_type = ForeignIdProperty("TaskTags")

    history = FieldProperty(s.Array(s.Bool))
    level = FieldProperty(s.Int(
        if_missing=0))

    @classproperty
    def name(cls):
        return cls.__mongometa__.name


class DBUser(MappedClass):
    class __mongometa__:
        name = "users"
        session = DBManager.add_session(name)
        unique_indexes = [('discord_id',)]

    _id = FieldProperty(s.ObjectId)
    join_date = FieldProperty(s.DateTime(required=True))
    ref_counter = FieldProperty(s.Int(
        if_missing=1))
    last_active = FieldProperty(s.DateTime(required=True))

    discord_id = FieldProperty(s.Int(required=True))
    chaster_name = FieldProperty(s.String)

    limits_message = FieldProperty(s.String(
        if_missing="This user has not yet set their limits message"))
    limit_tags = ForeignIdProperty("TaskTags", uselist=True)
    #limit_tasks = ForeignIdProperty("Tasks", uselist = True)

    kinks_message = FieldProperty(s.String(
        if_missing="This user has not yet set their kinks message"))
    kinks = ForeignIdProperty("UserKinks", uselist=True)
    main_kinks = FieldProperty(s.Array(s.String))

    special_statuses = FieldProperty(s.Object({
        "is_denied": s.Bool(if_missing=False),
        "is_locked": s.Bool(if_missing=False),
        "is_censored": s.Bool(if_missing=False),
        "cannot_scream": s.Bool(if_missing=False),
        "cannot_swear": s.Bool(if_missing=False),
        "cannot_unregister": s.Bool(if_missing=False)
    }))


    controller = ForeignIdProperty("DBUser", uselist=False)
    allow_requests = FieldProperty(s.Bool(if_missing=True))
    trusts = FieldProperty(s.Bool(if_missing=False))

    # To keep players who deleted/refreshed data blocked, discord_id is used instaead of _id.
    blocked = FieldProperty(s.Array(s.Int))

    @classproperty
    def name(cls):
        return cls.__mongometa__.name

    @classmethod
    def get_user(
        cls,
        *,
        discord_id: Optional[int] = None,
        db_id: Optional[ObjectId] = None,
        as_user: Optional[int] = None
    ) -> DBUser:
        """Returns the document of the asociated user.
        Raises ValueError if neither discord_id nor db_id is provided"""
        if db_id is not None:
            user = cls.query.get(_id=ObjectId(db_id))
        elif discord_id is not None:
            user = cls.query.find({"discord_id": discord_id}).first()
        else:
            raise ValueError(
                "Cannot get document without either a Discord ID or a Database ID")

        if user is None:
            raise UserNotRegisterd
        if as_user is not None and as_user in user.blocked:
            raise UserNotRegisterd

        return user

    @classmethod
    def change_setting(
            cls,
            setting: str,
            value: Any,
            discord_id: Optional[int] = None,
            db_id: Optional[ObjectId] = None,
            *,
            group: Optional[str] = None
    ):
        user = cls.get_user(discord_id=discord_id, db_id=db_id)

        if group is not None:
            user[group][setting] = value
        else:
            user[setting] = value

        DBManager.sessions[cls.name].flush()

    @classmethod
    def block(cls, blocker_id: int, to_block_id: int, *, unblock=False):
        user = cls.get_user(discord_id=blocker_id)
        if unblock:
            user.blocked.remove(to_block_id)
        else:
            if to_block_id in user.blocked:
                raise ValueError
            user.blocked.append(to_block_id)
        DBManager.sessions[cls.name].flush()

    @classmethod
    def get_owned(cls, db_id: ObjectId) -> List[DBUser]:
        return cls.query.find({"controller": db_id}).all()

    @classmethod
    def update(cls, discord_id: int, *, ref_count: Optional[int] = None):
        data = cls.query.find({"discord_id": discord_id})
        if data.count():
            user = data.first()
            user.last_active = datetime.utcnow()
        else:
            user = cls(
                discord_id=discord_id,
                last_active=datetime.utcnow(),
                join_date=datetime.utcnow()
            )
            user["controller"] = user._id

        if ref_count is not None:
            user.ref_counter = ref_count

        DBManager.sessions[cls.name].flush()

    @classmethod
    def set_controller(cls, owned_id: str, *, new_owner_id: str, trusts: bool = False):
        user = cls.get_user(db_id=owned_id)
        user["controller"] = new_owner_id
        user["trusts"] = trusts
        DBManager.sessions[cls.name].flush()

    @classmethod
    def join(cls, discord_id: int):
        data = cls.query.find({"discord_id": discord_id})
        if data.count():
            user = data.first()
            user.ref_counter += 1
        else:
            # A player who only joins a server should not be registered as having been active,
            # to be imediatly removed on leave. datetime.min to keep typing consistent
            user = cls(
                discord_id=discord_id,
                last_active=datetime.min,
                join_date=datetime.utcnow()
            )
            user["controller"] = user._id
        DBManager.sessions[cls.name].flush()

    @classmethod
    def leave(cls, discord_id: int, *, delete_time: timedelta):
        data = cls.query.find({"discord_id": discord_id})
        if data.count():
            user = data.first()
            user.ref_counter -= 1
            if (user.ref_counter <= 0) and (datetime.utcnow() - user.last_active > delete_time):
                cls.unregister(db_id=user._id)
            DBManager.sessions[cls.name].flush()

    @classmethod
    def register(cls, discord_id: int):
        if cls.query.find({"discord_id": discord_id}).count():
            raise UserAlreadyRegisterd
        user = cls(
            discord_id=discord_id,
            last_active=datetime.utcnow(),
            join_date=datetime.utcnow()
        )
        user["controller"] = user._id
        DBManager.sessions[cls.name].flush()

    @classmethod
    def unregister(
        cls,
        *, 
        discord_id: Optional[int] = None, 
        db_id: Optional[ObjectId] = None,
    ):
        user: DBUser = cls.get_user(discord_id=discord_id, db_id=db_id)

        owned: List[DBUser] = cls.get_owned(db_id=user._id)
        actually_owned = [owned_user for owned_user in owned if owned_user._id != user._id]
        for owned_user in actually_owned:
            cls.set_controller(owned_user._id, new_owner_id=owned_user._id)

        user.delete()
        DBManager.sessions[cls.name].flush()

    @classmethod
    def update_database(cls, user_ids: List[str], *, delete_time: timedelta):
        users = cls.query.find({}).all()
        for user in users:
            user.ref_counter = user_ids.count(user.discord_id)
            if (user.ref_counter <= 0) and (datetime.utcnow() - user.last_active > delete_time):
                # Unregister without the DB flush
                owned: List[DBUser] = cls.get_owned(db_id=user._id)
                actually_owned = [owned_user for owned_user in owned if owned_user._id != user._id]
                for owned_user in actually_owned:
                    cls.set_controller(owned_user._id, new_owner_id=owned_user._id)
                user.delete()
        DBManager.sessions[cls.name].flush()

    # Initialise the Reference Count Updater, and make it accessible for the scheduler.
    @classmethod
    def init_updater(cls, bot):
        global database_updater
        database_updater = RefCountUpdater(bot=bot)

    # TODO make this not just dump the database entry, and/or make it dump more stuff, like kink information and the like.

    @classmethod
    def get_settings(cls, discord_id: int) -> str:
        user = cls.get_user(discord_id=discord_id)
        user.last_active = datetime.utcnow()
        DBManager.sessions[cls.name].flush()
        return str(user)


Mapper.compile_all()
