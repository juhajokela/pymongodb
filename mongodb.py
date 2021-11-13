from copy import copy
from collections import OrderedDict

from pymongo import MongoClient
from bson.objectid import ObjectId

from fields import *  # TODO: refactor this


class Connection(object):

    # TODO: error message if attempting self.db before setup

    def __call__(self, database_url):
        client = MongoClient(database_url)
        self.db = client[database_url.split('/')[-1]]


connection = Connection()


class MetaModel(type):

    def __new__(cls, name, bases, attrs):

        # collect "local" fields
        attrs['fields'] = OrderedDict(
            (key, val) for key, val in attrs.items() if isinstance(val, Field)
        )
        new_cls = super().__new__(cls, name, bases, attrs)

        # collect fields from base classes
        fields = OrderedDict()
        for base in reversed(new_cls.__mro__):
            if hasattr(base, 'fields'):
                fields.update(base.fields)

        new_cls.fields = fields

        # collection
        if bases:
            new_cls.__collection__ = (
                attrs.get('__collection__') or name.lower()
            )
            new_cls._collection = connection.db[new_cls.__collection__]
        return new_cls


class Model(metaclass=MetaModel):

    '''
    QUESTION: How handle inconsistent database?
    (check _collection.replace_one and think _collection.find results handling)
    '''

    id = Field(required=False)

    ___collection__ = ''

    def __init__(self, **kwargs):
        validate = kwargs.pop('__validate', True)
        self._data = {}
        for key, field in self.fields.items():
            try:
                value = kwargs[key]
                if validate:
                    field.validate(value, raise_exception=True)
            except KeyError:
                if field.required:
                    raise AttributeError('field "{}" is required'.format(key))
                value = field.default
            except ValueError as e:
                raise e
            self._data[key] = value

    def __setattr__(self, key, value):
        field = getattr(self, key, None)
        if isinstance(field, Field):
            field.validate(value, raise_exception=True)
            self._data[key] = value
        else:
            super().__setattr__(key, value)

    def __getattr__(self, key):
        if key == '_data':
            raise AttributeError('_data is protected')
        value = super().__getattr__(key)
        if isinstance(value, Field):
            return self._data[key]
        return value

    def _upsert(self, data):
        _data = copy(data)
        _filter = {'_id': ObjectId(_data.pop('id', ''))}
        result = self._collection.update_one(
            _filter, {'$set': _data}, upsert=True
        )
        if result.upserted_id:
            self._data['id'] = result.upserted_id

    def save(self):
        # TODO: raise exception if write fails
        self._upsert(self._data)

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()
        return obj

    @classmethod
    def _build_query(self, query):
        if 'id' not in query:
            return query
        _query = copy(query)
        _query['_id'] = ObjectId(_query.pop('id'))
        return _query

    @classmethod
    def _from_db(cls, data):
        result = copy(data)
        result['id'] = str(result.pop('_id'))
        return cls(**result, __validate=False)

    @classmethod
    def get(cls, query, raise_exception=False):
        result = cls._collection.find(cls._build_query(query))
        if result is None or 1 < len(result):
            if raise_exception:
                # TODO: custom exceptions
                raise Exception('...')
            return None
        return cls._from_db(result)

    @classmethod
    def list(cls, query={}):
        query = cls._build_query(query)
        return [cls._from_db(x) for x in cls._collection.find(query)]

    def update(self, **kwargs):
        for key, value in kwargs.items():
            field = getattr(self, key)
            if not isinstance(field, Field):
                raise AttributeError('{} is not subclass of Field'.format(key))
            field.validate(value, raise_exception=True)
        data = {**self._data, **kwargs}
        self._upsert(data)
        self._data = data

    def delete(self):
        _id = self._data['id']
        if _id is None:
            raise Exception("Object doesn't exist in the database.")
        self._collection.delete_one({'_id': ObjectId(_id)})

    def __str__(self):
        values = ('{}={}'.format(f, self._data[f]) for f in self.fields)
        return '{}({})'.format(self.__class__.__name__, ', '.join(values))

    def __repr__(self):
        return str(self)
