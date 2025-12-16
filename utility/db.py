"""
MongoDB Database Connection Utilities
"""
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from .config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION
import certifi
import os


def get_mongo_client():
    """
    Create a MongoDB client with appropriate SSL settings.
    Uses SSL certificates for cloud MongoDB (contains 'mongodb+srv' or 'mongodb.net'),
    but not for local Docker MongoDB.
    """
    uri = MONGODB_URI or "mongodb://localhost:27017"
    
    # Determine if this is a cloud MongoDB (needs SSL) or local (no SSL)
    is_cloud_mongo = "mongodb+srv" in uri or "mongodb.net" in uri
    
    if is_cloud_mongo:
        return MongoClient(uri, serverSelectionTimeoutMS=4000, tlsCAFile=certifi.where())
    else:
        return MongoClient(uri, serverSelectionTimeoutMS=4000)


def ensure_mongo_collection():
    """
    Ensure MongoDB collection exists with proper indexes.
    Returns the collection or None if connection fails.
    """
    try:
        client = get_mongo_client()
        db = client[MONGODB_DB]
        coll = db[MONGODB_COLLECTION]
        
        # Check/create partial index on report_id
        index_name = "report_id_1"
        index_info = coll.index_information()
        
        if index_name in index_info:
            is_correct_index = index_info[index_name].get("partialFilterExpression") == {"report_id": {"$type": "string"}}
            if not is_correct_index:
                print(f"Dropping incorrect index '{index_name}'...")
                coll.drop_index(index_name)
                print("Index dropped.")
        
        # Create the correct partial index if it doesn't exist
        if index_name not in coll.index_information():
            print(f"Creating partial index '{index_name}'...")
            coll.create_index(
                "report_id",
                name=index_name,
                unique=True,
                partialFilterExpression={"report_id": {"$type": "string"}}
            )
            print("Index created.")
            
        return coll
    except Exception as e:
        print(f"MongoDB connection issue: {e}. Will continue without DB.")
        return None
