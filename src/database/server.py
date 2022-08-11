from typing import Any, Optional

from ming import schema as s
from ming.odm import FieldProperty
from ming.odm.declarative import MappedClass
from ming.odm import Mapper

from utils import classproperty
from .connect import DBManager


class ServerSettings(MappedClass):
    class __mongometa__:
        name = "server_settings"
        session = DBManager.add_session(name)
        unique_indexes = [('server_id',)]

    _id = FieldProperty(s.ObjectId)
    server_id = FieldProperty(s.Int(required=True))

    save_settings_on_leave = FieldProperty(s.Bool(
        if_missing=False))

    run_welcome_message = FieldProperty(s.Bool(
        if_missing=True))

    role_channel = FieldProperty(s.Int)

    # Initialising with the data from Lucifer's Lockup Lobby to give a valid starting point.
    welcome = FieldProperty(s.Object({
        "header_text": s.String(
            if_missing="Welcome to the Server!"),
        "main_channel": s.Int,
        "rules_button_channel": s.Int(
            if_missing=979527791148146688),
        "rules_button_text": s.String(
            if_missing="Rules"),
        "roles_button_channel": s.Int(
            if_missing=999107304437854248),
        "roles_button_text": s.String(
            if_missing="Role-select"),
        "guide_button_channel": s.Int(
            if_missing=999107209843707935),
        "guide_button_text": s.String(
            if_missing="Bot command guide")
    }))

    @classproperty
    def name(cls):
        return cls.__mongometa__.name

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
            f"header_text = '{self.welcome.header_text}'",
            f"main_channel = '{self.welcome.main_channel}'",
            f"rules_button_channel = '{self.welcome.rules_button_channel}'",
            f"rules_button_text = '{self.welcome.rules_button_text}'",
            f"roles_button_channel = '{self.welcome.roles_button_channel}'",
            f"roles_button_text = '{self.welcome.roles_button_text}'",
            f"guide_button_channel = '{self.welcome.guide_button_channel}'",
            f"guide_button_text = '{self.welcome.guide_button_text}'",
        ])
        return "\n\n".join([
            main,
            welcome
        ])

    @classmethod
    def enter_server(cls,
                     server_id: int,
                     *,
                     channel_id: int = 0,
                     welcome_message: str = "Welcome to the server!"
                     ):
        if not cls.query.find({"server_id": server_id}).count():
            cls(
                server_id=server_id,
                welcome={
                    "main_channel": channel_id,
                    "header_text": welcome_message
                }
            )
            DBManager.sessions[cls.name].flush()

    @classmethod
    def leave_server(cls, server_id: int):
        cls.query.remove({
            "server_id": server_id,
            "save_settings_on_leave": False
        })

    @classmethod
    def change_setting(cls,
                       server_id: int,
                       setting: str,
                       value: Any,
                       *,
                       group: Optional[str] = None
                       ):
        data = cls.query.find({"server_id": server_id})
        if not data.count():
            cls.enter_server(server_id)

        settings = data.first()
        if group is not None:
            settings[group][setting] = value
        else:
            settings[setting] = value
        DBManager.sessions[cls.name].flush()


Mapper.compile_all()
