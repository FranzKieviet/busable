import os
import pymongo
from pymongo import MongoClient, ReadPreference
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
from dotenv import load_dotenv

# Load local .env if present (useful for local dev)
load_dotenv()

MONGO_DATABASE_NAME = os.getenv("MONGO_DATABASE_NAME", "busable")

# Every agency's transit data lives in these two collections, and every region's places in the places collection.
# Only documents with is_active = True are served.
STOPS_COLLECTION_NAME = "stops"
ROUTES_COLLECTION_NAME = "routes"
PLACES_COLLECTION_NAME = "places"

def get_mongo_client():
    """
    Resolves MongoDB connection string with fallbacks for local dev vs Lambda:
    1. Check MONGO_URI
    2. Check MONGO_CONNECTION_STRING
    3. Fallback to local MongoDB instance (single node replica set, see scripts/docker-compose.yml)
    """
    mongo_uri = (
        os.getenv("MONGO_URI")
        or os.getenv("MONGO_CONNECTION_STRING")
        or "mongodb://localhost:27017/?directConnection=true"
    )
    return MongoClient(mongo_uri)


def _ensure_transit_indexes(db):
    stops = db[STOPS_COLLECTION_NAME]
    stops.create_index([("location", pymongo.GEOSPHERE), ("is_active", pymongo.ASCENDING)])
    stops.create_index([("stop_id", pymongo.ASCENDING), ("is_active", pymongo.ASCENDING)])
    stops.create_index([("agency", pymongo.ASCENDING), ("is_active", pymongo.ASCENDING)])

    routes = db[ROUTES_COLLECTION_NAME]
    routes.create_index([("route_id", pymongo.ASCENDING), ("is_active", pymongo.ASCENDING)])
    routes.create_index([("agency", pymongo.ASCENDING), ("is_active", pymongo.ASCENDING)])


def _ensure_places_indexes(db):
    places = db[PLACES_COLLECTION_NAME]
    places.create_index([("location", pymongo.GEOSPHERE), ("is_active", pymongo.ASCENDING)])
    places.create_index([("region", pymongo.ASCENDING), ("is_active", pymongo.ASCENDING)])


def _load_and_swap(client, docs_by_collection, scope_field: str, scope_value: str, load_id: str):
    """
    Replaces one scope's documents (an agency's transit data, or a region's places) without ever serving a partial load.

    1. Clear out inactive documents left behind by an earlier load of this scope that failed part way.
    2. Insert the new documents with is_active = False, so the API ignores them while they load.
    3. In one transaction, deactivate the scope's current documents and activate the new ones.
       Readers see either the old set or the new set, never a mix of the two.
    4. Delete the scope's now inactive (old) documents.

    docs_by_collection maps a collection to the list of new documents for it.
    Transactions require a replica set (Atlas, or the local single node replica set in scripts/docker-compose.yml).
    """
    scope_filter = {scope_field: scope_value}
    label = f"{scope_field} {scope_value}"

    # 1. Leftovers from a failed load
    for coll in docs_by_collection:
        stale = coll.delete_many({**scope_filter, "is_active": False}).deleted_count
        if stale:
            print(f"Removed {stale} {coll.name} left inactive by an earlier load of {label}")

    # 2. Insert the new load as inactive
    for coll, docs in docs_by_collection.items():
        for doc in docs:
            doc[scope_field] = scope_value
            doc["is_active"] = False
            doc["load_id"] = load_id
        coll.insert_many(docs, ordered=False)
        print(f"Inserted {len(docs)} {coll.name} for {label} (load {load_id}, inactive)")

    # 3. Swap old and new in one transaction
    def swap(session):
        for coll in docs_by_collection:
            coll.update_many({**scope_filter, "is_active": True}, {"$set": {"is_active": False}}, session=session)
            coll.update_many({**scope_filter, "load_id": load_id}, {"$set": {"is_active": True}}, session=session)

    with client.start_session() as session:
        session.with_transaction(
            swap,
            read_concern=ReadConcern("snapshot"),
            write_concern=WriteConcern("majority"),
            read_preference=ReadPreference.PRIMARY,
        )
    print(f"Activated load {load_id} for {label}")

    # 4. Remove the previous load
    for coll in docs_by_collection:
        old = coll.delete_many({**scope_filter, "is_active": False}).deleted_count
        print(f"Deleted {old} {coll.name} from the previous load of {label}")


def load_agency_transit_data(agency: str, stops: list, routes: list, load_id: str):
    """Swaps in a new load of one agency's stops and routes. See _load_and_swap."""
    if not stops or not routes:
        raise ValueError(f"Refusing to load agency {agency}: {len(stops)} stops and {len(routes)} routes. The current data is left in place.")

    client = get_mongo_client()
    db = client[MONGO_DATABASE_NAME]
    _ensure_transit_indexes(db)
    _load_and_swap(
        client,
        {db[STOPS_COLLECTION_NAME]: stops, db[ROUTES_COLLECTION_NAME]: routes},
        scope_field="agency",
        scope_value=agency,
        load_id=load_id,
    )


def load_region_places(region: str, places: list, load_id: str):
    """Swaps in a new load of one region's places. See _load_and_swap."""
    if not places:
        raise ValueError(f"Refusing to load region {region}: no places. The current data is left in place.")

    client = get_mongo_client()
    db = client[MONGO_DATABASE_NAME]
    _ensure_places_indexes(db)
    _load_and_swap(
        client,
        {db[PLACES_COLLECTION_NAME]: places},
        scope_field="region",
        scope_value=region,
        load_id=load_id,
    )
