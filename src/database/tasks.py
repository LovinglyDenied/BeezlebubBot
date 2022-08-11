from ming import schema as s
from ming.odm import FieldProperty
from ming.odm.property import ForeignIdProperty, RelationProperty
from ming.odm.declarative import MappedClass
from ming.odm import Mapper

from utils import classproperty
from .connect import DBManager


class TaskTags(MappedClass):
    class __mongometa__:
        name = "task_tags"
        session = DBManager.add_session(name)
        unique_indexes = [('name',)]

    _id = FieldProperty(s.ObjectId)
    name = FieldProperty(s.String)

    associated_status = FieldProperty(s.Array(s.String))

    max_level = FieldProperty(s.Int(
        if_missing=5))

    @classproperty
    def name(cls):
        return cls.__mongometa__.name

    @classmethod
    def register_tag(cls, name: str):
        cls(name=name.lower().strip())

    @classmethod
    def get_all(cls):
        for tag in cls.qeuery.find().all():
            yield tag


class Tasks(MappedClass):
    class __mongometa__:
        name = "tasks"
        session = DBManager.add_session(name)

    _id = FieldProperty(s.ObjectId)

    @classproperty
    def name(cls):
        return cls.__mongometa__.name


Mapper.compile_all()
