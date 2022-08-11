from typing import Optional

from ming import create_datastore
from ming.odm import ThreadLocalODMSession
from ming.datastore import DataStore

from pymongo import MongoClient
from pymongo.database import Database

from utils import classproperty


class DatabaseConnectionError(Exception):
    """The database singleton was called without it being connected
    or singleton init called with it already being connected."""
    pass


class FaultyDatabase(Exception):
    """The initialised database appeared to not have been of the correct type."""
    pass


class DBManager:
    """Database wrapper singleton, controlls the connection to the MongoDB client
    initialised with a Ming uri.

    attributes:
    - datastore: the ming DataStore object
    - sessions: the ming ThreadLocalODMSession objects, accessed through a dict.
    - db: the PyMongo Database object
        - db.client: the PyMongo MongoClient object
        - db.name: the name of the database the Ming uri made the DataStore connect to.

    Raises DatabaseConnectionError if the database is either connected to multiple times or not at all
    Raises FaultyDatabase if the database object is not initialised to get the expected attributes"""

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, *, uri: Optional[str] = None):
        cls = self.__class__
        if uri:
            if hasattr(cls, "_uri"):
                raise DatabaseConnectionError
            cls._uri: str = uri
            cls.sessions: dict = {}

            cls.datastore: DataStore = create_datastore(uri)
            # If it looks like a duck and quacks like a duck, it might still trow an error
            if not isinstance(cls.datastore.db, Database):
                raise FaultyDatabase
            if not isinstance(cls.datastore.db.client, MongoClient):
                raise FaultyDatabase

        if not hasattr(cls, "_uri"):
            raise DatabaseConnectionError

    @classproperty
    def db(cls):
        """The underling Database from PyMongo
        Has the attribures:
        - db.client to get to the underlying MongoClient
        - db.name to get the Database name as a string"""
        db: Database = cls.datastore.db
        return db

    @classmethod
    def add_session(cls, name: str):
        """adds a ming ThreadLocalODMSession to the .sessions dict, and returns it."""
        cls.sessions[name]: ThreadLocalODMSession = ThreadLocalODMSession(
            bind=cls.datastore)
        return cls.sessions[name]
