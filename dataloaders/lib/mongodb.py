import os
import pymongo
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from dotenv import load_dotenv

# Load local .env if present (useful for local dev)
load_dotenv()

MONGO_DATABASE_NAME = os.getenv("MONGO_DATABASE_NAME", "busable")

def get_mongo_client():
    """
    Resolves MongoDB connection string with fallbacks for local dev vs Lambda:
    1. Check MONGO_URI
    2. Check MONGO_CONNECTION_STRING
    3. Fallback to local MongoDB instance (mongodb://localhost:27017)
    """
    mongo_uri = (
        os.getenv("MONGO_URI") 
        or os.getenv("MONGO_CONNECTION_STRING") 
        or "mongodb://localhost:27017"
    )
    return MongoClient(mongo_uri)


def upload_data(data, collection_name: str):
    """
    Uploads a list of dictionaries to MongoDB (local or Atlas).
    """
    if isinstance(data, dict):
        data = list(data.values())

    if not data:
        print("No data provided to upload.")
        return

    if not isinstance(data, (list, tuple)):
        raise TypeError("upload_data expects a list of documents or a dict mapping IDs to documents")

    if isinstance(data, (list, tuple)) and data and not isinstance(data[0], dict):
        raise TypeError("upload_data expects each item in the list to be a document dict")

    try:
        # Use get_mongo_client() for connection resolution
        client = get_mongo_client()
        db = client[MONGO_DATABASE_NAME]
        collection = db[collection_name]

        print(f"Connecting to database: '{MONGO_DATABASE_NAME}' -> Collection: '{collection_name}'...")

        # Bulk insert
        result = collection.insert_many(data)

        # Ensure spatial index is built on 2dsphere fields
        try:
            collection.create_index([("location", pymongo.GEOSPHERE)])
        except Exception as ie:
            print(f"Index creation note for {collection_name}: {ie}")

        print(f"Successfully uploaded {len(result.inserted_ids)} documents to {MONGO_DATABASE_NAME}.{collection_name}!")

    except BulkWriteError as bwe:
        print(f"A bulk write error occurred. Details: {bwe.details}")
    except Exception as e:
        print(f"An unexpected error occurred while uploading to MongoDB: {e}")