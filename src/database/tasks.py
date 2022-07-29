from ming import schema as s
from ming.odm import FieldProperty
from ming.odm.property import ForeignIdProperty, RelationProperty
from ming.odm.declarative import MappedClass

from ming.odm import Mapper

from .connect import database_session


class TaskTags(MappedClass):
    class __mongometa__:
        session = database_session
        name = "task_tags"
        unique_indexes = [('name',)]

    _id  = FieldProperty(s.ObjectId)
    name = FieldProperty(s.String)

    associated_status = FieldProperty(s.Array(s.String))

    max_level = FieldProperty(s.Int(
        if_missing = 5))

    @classmethod
    def register_tag(cls, name:str):
        cls(name = name.lower().strip())

    @classmethod
    def get_all(cls):
        for tag in cls.qeuery.find().all():
            yield tag

class Tasks(MappedClass):
    class __mongometa__:
        session = database_session
        name = "tasks"

    _id = FieldProperty(s.ObjectId)

Mapper.compile_all()
