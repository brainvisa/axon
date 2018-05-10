from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
import six

class_to_class_name = {
    str:     'unicode',
    unicode: 'unicode',
    bool:    'bool',
    list:    'list',
    tuple:   'list',
    int:     'int',
    float:   'float',
}


class FedjiMongo(MongoClient):

    def __getattr__(self, db):
        return FedjiMongoDB(self, db)


class FedjiMongoDB(Database):
    # def __init__(self, fedji_client, db):
        # self.db = getattr(fedji_client.client, db)

    def __getattr__(self, collection):
        return FedjiMongoCollection(self, collection)


class FedjiMongoCollection(Collection):

    def __init__(self, fedji_db, collection):
        Collection.__init__(self, fedji_db, collection)
        attributes_collection = Database.__getattr__(
            self.database, '_attributes')
        fields = attributes_collection.find_one({})
        if fields is None:
            self.fields_id = attributes_collection.save({}, manipluate=True)
            self._fields = {}
        else:
            self.fields_id = fields.pop('_id')
            self._fields = fields

    @property
    def fields(self):
        return self._fields

    def new_field(self, field, cls):
        if field not in self.fields:
            atype = class_to_class_name[cls]
            self._fields[field] = atype
            doc = self.fields.copy()
            doc['_id'] = self.fields_id
            attributes_collection = Database.__getattr__(
                self.database, '_attributes')
            import pprint
            pprint.pprint(doc)
            attributes_collection.save(doc)

    def insert(self, doc_or_docs, **kwargs):
        if isinstance(doc_or_docs, dict):
            doc_or_docs = [doc_or_docs]
        for document in doc_or_docs:
            for k, v in six.iteritems(document):
                self.new_field(k, v.__class__)
        Collection.insert(self, doc_or_docs, **kwargs)

    # def __getattr__(self, attribute):
        # return getattr(self.collection, attribute)
