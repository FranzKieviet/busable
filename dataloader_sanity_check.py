def print_route_stop_names(route_id, db_name=None, route_collection_names=None, stop_collection_names=None):
    """
    Prints the stop names in order for a route document such as:
    ac-transit_route_6_0
    """
    connection_string = os.getenv(
        "MONGO_CONNECTION_STRING",
        "mongodb://admin:devpassword@localhost:27017/?authSource=admin"
    )
    db_name = db_name or os.getenv("MONGO_DATABASE_NAME", "busable_main")

    client = MongoClient(connection_string)
    try:
        db = client[db_name]

        if route_collection_names is None:
            route_collection_names = [
                name for name in db.list_collection_names()
                if name.startswith("routes")
            ] or ["routes"]

        route_doc = None
        for collection_name in route_collection_names:
            route_doc = db[collection_name].find_one({"_id": route_id})
            if route_doc:
                break

        if not route_doc:
            print(f"No route found for {route_id} in database '{db_name}'")
            return []

        ordered_stops = route_doc.get("ordered_stops", [])
        if not ordered_stops:
            print(f"Route {route_id} has no ordered stops")
            return []

        stop_ids = [stop.get("stop_id") for stop in ordered_stops if stop.get("stop_id")]

        if stop_collection_names is None:
            stop_collection_names = [
                name for name in db.list_collection_names()
                if name.startswith("stops")
            ] or ["stops"]

        stop_name_by_id = {}
        for collection_name in stop_collection_names:
            stop_docs = list(db[collection_name].find(
                {
                    "$or": [
                        {"_id": {"$in": stop_ids}},
                        {"stop_id": {"$in": stop_ids}}
                    ]
                },
                {"_id": 1, "stop_name": 1, "stop_id": 1}
            ))
            if stop_docs:
                for stop_doc in stop_docs:
                    stop_name_by_id[stop_doc.get("_id")] = stop_doc.get("stop_name", "Unknown stop")
                    stop_name_by_id[stop_doc.get("stop_id")] = stop_doc.get("stop_name", "Unknown stop")
                break

        ordered_names = [
            stop_name_by_id.get(stop.get("stop_id"), "Unknown stop")
            for stop in ordered_stops
            if stop.get("stop_id")
        ]

        print(f"Route {route_id} stop names:")
        for index, stop_name in enumerate(ordered_names, start=1):
            print(f"{index}. {stop_name}")

        return ordered_names
    finally:
        client.close()