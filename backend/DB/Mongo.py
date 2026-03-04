from pymongo import MongoClient

class MongoDBConnection:
    def __init__(self, db_name: str = "db_main", host: str = "mongodb://mongodb:27017"):
        self.host = host
        self.db_name = db_name

        self.mongo_client = MongoClient(self.host)
        
        self.mongo_db = self.mongo_client[self.db_name]

    
    def get_collection(self, collection_name: str):
        """ Get a collection from the database """

        return self.mongo_db[collection_name]

    def insert_one(self, collection_name: str, data: dict):
        """ Insert a single document into the collection """

        collection = self.get_collection(collection_name)
        result = collection.insert_one(data)
        return result
    
    def find_one(self, collection_name: str, query: dict):
        """ Find a single document in the collection """

        collection = self.get_collection(collection_name)
        result = collection.find_one(query)
        return result
    
    def find_all(self, collection_name: str, query: dict = {}):
        """ Find all documents in the collection """

        collection = self.get_collection(collection_name)
        results = collection.find(query)
        return list(results)

    def close(self):
        """ Close the MongoDB connection """

        self.mongo_client.close()

