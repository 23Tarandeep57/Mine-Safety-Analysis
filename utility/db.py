from pymongo import MongoClient
from pymongo.errors import PyMongoError
from .config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION

def ensure_mongo_collection():
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=4000)
        db = client[MONGODB_DB]
        coll = db[MONGODB_COLLECTION]
        
        # Ensure the correct index is in place
        index_name = "report_id_1"
        index_info = coll.index_information()
        
        if index_name in index_info:
            # Check if the existing index is the correct partial index
            is_correct_index = index_info[index_name].get("partialFilterExpression") == {"report_id": {"$type": "string"}}
            if not is_correct_index:
                print(f"Dropping incorrect index '{index_name}'...")
                coll.drop_index(index_name)
                print("Index dropped.")
        
        # Create the correct partial index if it doesn't exist
        # Re-check index_information after potential drop
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
