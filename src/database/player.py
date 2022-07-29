from typing import Any, List, Optional
from datetime import datetime, timedelta

from ming import schema as s
from ming.odm import FieldProperty
from ming.odm.property import ForeignIdProperty, RelationProperty
from ming.odm.declarative import MappedClass

from ming.odm import Mapper

from .connect import database_session
from .tasks import TaskTags, Tasks

delete_time = timedelta(days=90)

class PlayerAlreadyRegisterd(Exception):
    pass
class PlayerNotRegisterd(Exception):
    pass

class PlayerKinks(MappedClass):
    class __mongometa__:
        session = database_session
        name = "player_kinks"
    
    _id = FieldProperty(s.ObjectId)
    kink_type = ForeignIdProperty("TaskTags")

    history = FieldProperty(s.Array(s.Bool))
    level = FieldProperty(s.Int(
        if_missing = 0))


class Player(MappedClass):
    class __mongometa__:
        session = database_session
        name = "player"
        unique_indexes = [('discord_id',)]

    _id = FieldProperty(s.ObjectId)
    join_date = FieldProperty(s.DateTime(required=True))
    ref_counter = FieldProperty(s.Int(
        if_missing = 1))
    last_active = FieldProperty(s.DateTime(required=True))

    discord_id = FieldProperty(s.Int(required=True))

    limit_message = FieldProperty(s.String(
            if_missing = "This user has not jet set their limit message"))
    limit_tags = ForeignIdProperty("TaskTags", uselist = True)
    #limit_tasks = ForeignIdProperty("Tasks", uselist = True)

    kinks = ForeignIdProperty("PlayerKinks", uselist = True)
    main_kinks = FieldProperty(s.Array(s.String))

    special_statuses = FieldProperty(s.Object({
        "denied": s.Bool(if_missing = False),
        "locked": s.Bool(if_missing = False),
        "censor": s.Bool(if_missing = False),
        "scream": s.Bool(if_missing = False),
        "swear" : s.Bool(if_missing = False)
    }))
    
    _controls = ForeignIdProperty("Player", uselist=True)
    controls = RelationProperty("Player", via=("_controls", True))
    controlled_by = RelationProperty("Player", via=("_controls", False))
    trusts = FieldProperty(s.Bool(if_missing = False))

    # To keep players who deleted/refreshed data blocked, discord_id is used instaead of _id. 
    blocked = FieldProperty(s.Array(s.Int))

    # def __str__(self):
    #     pass

    @classmethod
    def change_setting(cls, discord_id:int, setting:str, value:Any, *, group:Optional[str] = None):
        data = cls.query.find({"discord_id": discord_id})
        if not data.count(): raise PlayerNotRegisterd

        user = data.first()
        if group is not None: 
            user[group][setting] = value
        else:
            user[setting] = value
        database_session.flush()

    @classmethod
    def update(cls, discord_id:int):
        data = cls.query.find({"discord_id": discord_id})
        if data.count():
            user = data.first()
            user.last_active = datetime.utcnow()
        else:
            user = cls(discord_id = discord_id, last_active = datetime.utcnow(), join_date = datetime.utcnow())
            user["controls"] = [user]
        database_session.flush()

    @classmethod
    def join(cls, discord_id:int):
        data = cls.query.find({"discord_id": discord_id})
        if data.count(): 
            user = data.first()
            user.ref_counter += 1
        else:
            #A player who only joins a server should not be registered as having been active,
            #to be imediatly removed on leave. datetime.min to keep typing consistent
            user = cls(discord_id = discord_id, last_active = datetime.min, join_date = datetime.utcnow())
            user["controls"] = [user]
        database_session.flush()

    @classmethod
    def leave(cls, discord_id:int):
        data = cls.query.find({"discord_id": discord_id})
        if data.count():
            user = data.first()
            user.ref_counter -= 1
            if (user.ref_counter <= 0) and (datetime.utcnow() - user.last_active > delete_time): 
                user.delete()
            database_session.flush()

    @classmethod
    def register(cls, discord_id:int):
        if cls.query.find({"discord_id": discord_id}).count(): raise PlayerAlreadyRegisterd
        user = cls(discord_id = discord_id, last_active = datetime.utcnow(), join_date = datetime.utcnow())
        user["controls"] = [user]
        database_session.flush()
    
    @classmethod
    def unregister(cls, discord_id:int):
        data = cls.query.find({"discord_id": discord_id}) 
        if not data.count(): raise PlayerNotRegisterd
        data.first().delete()
        database_session.flush()

    @classmethod
    def update_database(cls, user_ids: List[str]):
        users = cls.query.find({}).all()
        for user in users:
            user.ref_counter = user_ids.count(user.discord_id)
            if (user.ref_counter <= 0) and (datetime.utcnow() - user.last_active > delete_time): 
                user.delete()
        database_session.flush()

    #TODO make this not just dump the database entry, and/or make it dump more stuff.
    #This is a seperate entry, to allow people to do /getsettings to confirm their data has been removed.
    @classmethod
    def get_settings(cls, discord_id:int):
        data = cls.query.find({"discord_id": discord_id})
        if not data.count(): raise PlayerNotRegisterd
        user = data.first()
        user.last_active = datetime.utcnow()
        database_session.flush()
        return user

Mapper.compile_all()

