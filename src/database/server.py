from typing import Any, Optional

from ming import schema as s
from ming.odm import FieldProperty
from ming.odm.declarative import MappedClass

from ming.odm import Mapper

from .connect import database_session

class ServerSettings(MappedClass):
    class __mongometa__:
        session = database_session
        name = "server_settings"
        unique_indexes = [('server_id',)]

    _id = FieldProperty(s.ObjectId)
    server_id = FieldProperty(s.Int(required=True))

    save_settings_on_leave = FieldProperty(s.Bool(
            if_missing = False))

    run_welcome_message = FieldProperty(s.Bool(
            if_missing = True))
    
    role_channel = FieldProperty(s.String)

    #Making sure to give every setting a plausable value
    #The API otherwise trows an HTTP error, difficult to debug for users
    welcome = FieldProperty(s.Object({
        "welcome_message": s.String(
            if_missing = "Welcome to the Server!"),
        "welcome_channel": s.Int,
        "rules_link": s.String(
            if_missing = "https://discord.com/channels/979520017215393852/979527791148146688"),
        "rules_message": s.String(
            if_missing = "Rules"),
        "roles_link": s.String(
            if_missing = "https://discord.com/channels/979520017215393852/999107304437854248"),
        "roles_message": s.String(
            if_missing = "Role-select"),
        "guide_link": s.String(
            if_missing = "https://discord.com/channels/979520017215393852/999107209843707935"),
        "guide_message": s.String(
            if_missing = "Bot command guide")
        }))

    def __str__(self):
        main = "\n".join([
            f"== Main settings ==",
            f"server_id = '{self.server_id}'",
            f"save_settings_on_leave = '{self.save_settings_on_leave}'",
            f"run_welcome_message = '{self.run_welcome_message}'",
            f"role_channel = '{self.role_channel}'"
            ])
        welcome = "\n".join([
            f"== Welcome Message ==",
            f"welcome_message = '{self.welcome.welcome_message}'",
            f"welcome_channel = '{self.welcome.welcome_channel}'",
            f"rules_link = '{self.welcome.rules_link}'",
            f"rules_message = '{self.welcome.rules_message}'",
            f"roles_link = '{self.welcome.roles_link}'",
            f"roles_message = '{self.welcome.roles_message}'",
            f"guide_link = '{self.welcome.guide_link}'",
            f"guide_message = '{self.welcome.guide_message}'",
            ])
        return "\n\n".join([
                main,
                welcome
                ])

    @classmethod
    def enter_server(cls,
            server_id:int, 
            *, 
            channel_id:int = 0, 
            welcome_message:str = "Welcome to the server!"
            ):
        if not cls.query.find({"server_id": server_id}).count():
            cls(
                server_id = server_id, 
                welcome = {
                    "welcome_channel": channel_id,
                    "welcome_message": welcome_message
                    }
                )
            database_session.flush()
    
    @classmethod
    def leave_server(cls, server_id:int):
        cls.query.remove({
            "server_id": server_id, 
            "save_settings_on_leave": False
        })

    @classmethod
    def change_setting(cls, 
            server_id:int, 
            setting:str, 
            value:Any, 
            *, 
            group:Optional[str] = None
            ):
        data = cls.query.find({"server_id": server_id})
        if not data.count(): cls.enter_server(server_id)

        settings = data.first()
        if group is not None: 
            settings[group][setting] = value
        else:
            settings[setting] = value
        database_session.flush()

Mapper.compile_all()
