import os
import pymongo
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

MONGO_DATABASE_NAME = os.getenv("MONGO_DATABASE_NAME", "busable_feat_routing")  # TODO remember to set this in terraform

def upload_data(data, collection_name: str):
    """
    Uploads a list of dictionaries to the local MongoDB instance.
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

    # 1. Pull connection info from environment, or fall back to your Docker defaults
    connection_string = os.getenv(
        "MONGO_CONNECTION_STRING", 
        "mongodb://admin:devpassword@localhost:27017/?authSource=admin "#TODO Update this when mvoing to production
    )

    try:
        # 2. Connect to the MongoDB client
        client = MongoClient(connection_string)
        db = client[MONGO_DATABASE_NAME]
        collection = db[collection_name]

        print(f"Connecting to database: '{MONGO_DATABASE_NAME}' -> Collection: '{collection_name}'...")

        # 3. Use insert_many for high-performance bulk operations
        result = collection.insert_many(data)
        # Create geospatial index on the `location` field if present
        try:
            collection.create_index([("location", pymongo.GEOSPHERE)])
        except Exception as ie:
            print(f"Failed to create geospatial index on {collection_name}: {ie}")

        print(f"Successfully uploaded {len(result.inserted_ids)} documents to {MONGO_DATABASE_NAME}.{collection_name}!")

    except BulkWriteError as bwe:
        print(f"A bulk write error occurred. Details: {bwe.details}")
    except Exception as e:
        print(f"An unexpected error occurred while uploading to MongoDB: {e}")
    finally:
        client.close()