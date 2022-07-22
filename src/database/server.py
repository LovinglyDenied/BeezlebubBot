from typing import Any

from ming import create_datastore
from ming.odm import ThreadLocalODMSession

from ming import schema
from ming.odm import FieldProperty
from ming.odm.declarative import MappedClass

from ming.odm import Mapper

from .connect import database_session

class ServerSettings(MappedClass):
    class __mongometa__:
        session = database_session
        name = "server_settings"
        unique_indexes = [('server_id',)]

    _id = FieldProperty(schema.ObjectId)
    server_id = FieldProperty(schema.Int)

    save_settings_on_leave = FieldProperty(schema.Bool(
            if_missing = False))

    run_welcome_message = FieldProperty(schema.Bool(
            if_missing = True))
    
    role_channel = FieldProperty(schema.String )

    #Making sure to give every setting a plausable value
    #The API otherwise trows an HTTP error, difficult to debug for users
    welcome = FieldProperty(schema.Object({
        "welcome_message": schema.String(
            if_missing = "Welcome to the Server!"),
        "welcome_channel": schema.Int,
        "rules_link": schema.String(
            if_missing = "https://discord.com/channels/979520017215393852/979527791148146688"),
        "rules_message": schema.String(
            if_missing = "Rules"),
        "roles_link": schema.String(
            if_missing = "https://discord.com/channels/979520017215393852/999107304437854248"),
        "roles_message": schema.String(
            if_missing = "Role-select"),
        "guide_link": schema.String(
            if_missing = "https://discord.com/channels/979520017215393852/999107209843707935"),
        "guide_message": schema.String(
            if_missing = "Bot command guide")
        }))
    
    @classmethod
    def enter_server(cls, server_id:int, channel_id:int):
        if not cls.query.find({"server_id": server_id}).count():
            cls(server_id = server_id, welcome = {"welcome_channel": channel_id})
            database_session.flush()
    
    @classmethod
    def leave_server(cls, server_id:int):
        cls.query.remove({
            "server_id": server_id, 
            "save_settings_on_leave": False
        })

    @classmethod
    def change_setting(cls, server_id:int, setting:str, value:Any, *, group = None):
        settings = cls.query.find({"server_id": server_id}).first()
        if group is not None: 
            settings[group][setting] = value
        else:
            settings[setting] = value
        database_session.flush()

    #TODO make this not just dump the database entry
    @classmethod
    def get_settings(cls, server_id:int):
        return cls.query.find({"server_id": server_id}).first()


Mapper.compile_all()
