from pymongo import MongoClient
from pymongo.errors import PyMongoError
from .config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION

def ensure_mongo_collection():
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=4000)
        db = client[MONGODB_DB]
        coll = db[MONGODB_COLLECTION]
        try:
            coll.create_index("report_id", unique=True)
        except Exception:
            pass
        return coll
    except Exception as e:
        print(f"MongoDB connection issue: {e}. Will continue without DB.")
        return None
