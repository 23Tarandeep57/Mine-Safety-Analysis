import os
import sys
import pymongo
from dotenv import load_dotenv

MONGO_DB_NAME = "mines_safety"             # The name of your database
MONGO_COLLECTION_NAME = "dgms_reports"  # The name of your collection
# MONGO_FIELD_TO_SEARCH = "description"      # The field that contains the text you want to search

# Load .env file
load_dotenv()
MONGO_CONNECTION_STRING = os.getenv("MONGODB_URI")

if not MONGO_CONNECTION_STRING:
    print("Error: MONGO_CONNECTION_STRING not found in .env file.")
    sys.exit(1)

compound_text_index = [
    ("mine_details.name", "text"),
    ("incident_details.brief_cause", "text"),
    ("incident_details.cause_code", "text"),
    ("best_practices", "text"),
    ("summary", "text"),
    ("_raw_title", "text")
]

client = None

try:
    print("Connecting to MongoDB...")
    client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
    
    # Ping the server to confirm connection
    client.admin.command('ping')
    print("MongoDB connection successful.")

    db = client[MONGO_DB_NAME]
    collection = db[MONGO_COLLECTION_NAME]
    
    print(f"Creating compound text index on collection: '{MONGO_COLLECTION_NAME}'...")
    
    # Create the compound text index
    index_name = collection.create_index(compound_text_index, name="RAG_Text_Index")
    
    print(f"\nSuccessfully created index: '{index_name}'")
    print("The index now covers the following fields:")
    for field, _ in compound_text_index:
        print(f"  - {field}")

except pymongo.errors.OperationFailure as e:
    print(f"\n--- ERROR ---")
    print(f"An error occurred: {e}")
    print("\nThis can happen if a text index with different fields already exists.")
    print("Please drop any existing text indexes on this collection using MongoDB Atlas/Compass and try again.")
except Exception as e:
    print(f"\nAn error occurred: {e}")
    
finally:
    if client:
        client.close()
        print("\nMongoDB connection closed.")