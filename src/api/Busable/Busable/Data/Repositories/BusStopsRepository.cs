using Busable.Business.Objects;
using Busable.Data.Interfaces;
using Busable.Data.Objects;
using Busable.Data.Utilities;
using MongoDB.Bson;
using MongoDB.Driver;

namespace Busable.Data.Repositories
{
    public class BusStopRepository : IBusStopsRepository
    {
        private QueryHelper _queryHelper;
        private readonly IMongoDatabase _database;
        private readonly string _stopsCollectionName;
        private readonly string _routesCollectionName;
        private const int MAX_TIME = 900; //15 mins in seconds
        private readonly ILogger<BusStopRepository> _logger;

        public BusStopRepository(IMongoDatabase database, string stopsCollectionName, string routesCollectionName, ILogger<BusStopRepository> logger)
        {
            _database = database ?? throw new ArgumentNullException(nameof(database));
            _stopsCollectionName = stopsCollectionName ?? throw new ArgumentNullException(nameof(stopsCollectionName));
            _routesCollectionName = routesCollectionName ?? throw new ArgumentNullException(nameof(routesCollectionName));
            _queryHelper = new QueryHelper();
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));

            _logger.LogInformation("BusStopRepository initialized with database '{DatabaseName}' and collections: '{Stops}' and '{Routes}'", _database.DatabaseNamespace.DatabaseName, _stopsCollectionName, _routesCollectionName);
        }

        private IMongoCollection<BsonDocument> GetStopsCollection() => _database.GetCollection<BsonDocument>(_stopsCollectionName);
        private IMongoCollection<BsonDocument> GetRoutesCollection() => _database.GetCollection<BsonDocument>(_routesCollectionName);

        // The dataloader inserts each agency's new data as inactive, then swaps it to active in one transaction.
        // Only active documents are ever served.
        private static readonly FilterDefinition<BsonDocument> ActiveFilter = Builders<BsonDocument>.Filter.Eq("is_active", true);

        // A query that is still reading while a swap commits can pick up both the old and new copy of a stop.
        // Keep the first copy of each stop id so callers never see duplicates.
        private static List<BusStop> DistinctById(IEnumerable<BusStop> stops) => stops.GroupBy(s => s.Id).Select(g => g.First()).ToList();

        public async Task<List<BusStop?>> GetNearestBusStopAsync(double latitude, double longitude, double maxDistanceM)
        {
            _logger.LogInformation("GetNearestBusStopAsync called. Lat: {Lat}, Lng: {Lng}, Radius: {Dist}m", latitude, longitude, maxDistanceM);
            var docs = await _queryHelper.GetNearestAsync(GetStopsCollection(), latitude, longitude, maxDistanceM, ActiveFilter);
            _logger.LogInformation("Mongo Query returned {Count} raw documents.", docs?.Count ?? 0);
            return DistinctById(docs?.Select(doc => MapDocument(doc, latitude, longitude)) ?? Enumerable.Empty<BusStop>()).ToList<BusStop?>();
        }

        public async Task<DownstreamRouteDbo> GetDownstreamStopsAsync(string targetRouteId, string originStopId)
        {
            var pipeline = new BsonDocument[]
            {
                // Stage 1: Match the active copy of the route
                new BsonDocument("$match",
                    new BsonDocument
                    {
                        { "route_id", targetRouteId },
                        { "is_active", true }
                    }),

                // Stage 2: Calculate origin index and find matched stop
                new BsonDocument("$addFields", new BsonDocument
                {
                    {
                        "originIdx",
                        new BsonDocument("$indexOfArray",
                            new BsonArray
                            {
                                "$ordered_stops.stop_id",
                                originStopId
                            })
                    },
                    {
                        "matchedStop",
                        new BsonDocument("$arrayElemAt",
                            new BsonArray
                            {
                                new BsonDocument("$filter",
                                    new BsonDocument
                                    {
                                        {
                                            "input", "$ordered_stops"
                                        },
                                        {
                                            "as", "stop"
                                        },
                                        {
                                            "cond",
                                            new BsonDocument("$eq",
                                                new BsonArray
                                                {
                                                    "$$stop.stop_id",
                                                    originStopId
                                                })
                                        }
                                    }),
                                0
                            })
                    }
                }),

                // Stage 3: Slice downstream stops and filter by cumulative time
                new BsonDocument("$project",
                    new BsonDocument
                    {
                        { "_id", 0 },
                        { "route_id", 1 },
                        { "route_short_name", 1 },
                        { "origin_cumulative_time_sec", "$matchedStop.cumulative_time_sec" },
                        {
                            "downstream_stops",
                            new BsonDocument("$filter",
                                new BsonDocument
                                {
                                    {
                                        "input",
                                        new BsonDocument("$slice",
                                            new BsonArray
                                            {
                                                "$ordered_stops",
                                                new BsonDocument("$add",
                                                    new BsonArray
                                                    {
                                                        "$originIdx",
                                                        1
                                                    }),
                                                new BsonDocument("$size",
                                                    "$ordered_stops")
                                            })
                                    },
                                    {
                                        "as", "stop"
                                    },
                                    {
                                        "cond",
                                        new BsonDocument("$lte",
                                            new BsonArray
                                            {
                                                "$$stop.cumulative_time_sec",
                                                new BsonDocument("$add",
                                                    new BsonArray
                                                    {
                                                        "$matchedStop.cumulative_time_sec",
                                                        MAX_TIME
                                                    })
                                            })
                                    }
                                })
                        }
                    })
            };
            var result = await GetRoutesCollection().Aggregate<DownstreamRouteDbo>(pipeline).FirstOrDefaultAsync();
            return result;
        }

        public async Task<List<BusStop>> GetBusStopsByIdsAsync(IEnumerable<string> stopIds)
        {
            var ids = stopIds.Distinct().ToList();
            _logger.LogInformation("GetBusStopsByIdsAsync called for {Count} stop ids", ids.Count);
            if (ids.Count == 0)
            {
                return new List<BusStop>();
            }

            var filter = Builders<BsonDocument>.Filter.And(Builders<BsonDocument>.Filter.In("stop_id", ids), ActiveFilter);
            var docs = await GetStopsCollection().Find(filter).ToListAsync();
            return DistinctById(docs.Select(doc => MapDocument(doc)));
        }

        private static BusStop MapDocument(BsonDocument doc, double? sourceLatitude = null, double? sourceLongitude = null)
        {
            var id = doc.GetValue("stop_id", BsonValue.Create(string.Empty)).ToString();
            var name = doc.GetValue("stop_name",
                        doc.GetValue("Name", doc.GetValue("name", BsonValue.Create(string.Empty))))
                    .ToString();

            double latitude = 0;
            double longitude = 0;

            if (doc.TryGetValue("location", out var locationValue) && locationValue.IsBsonDocument)
            {
                var locationDoc = locationValue.AsBsonDocument;
                if (locationDoc.TryGetValue("coordinates", out var coordsValue) && coordsValue.IsBsonArray)
                {
                    var coords = coordsValue.AsBsonArray;
                    if (coords.Count >= 2)
                    {
                        longitude = coords[0].ToDouble();
                        latitude = coords[1].ToDouble();
                    }
                }
            }

            if (latitude == 0 && longitude == 0)
            {
                latitude = doc.GetValue("Latitude", doc.GetValue("latitude", BsonValue.Create(0.0))).ToDouble();
                longitude = doc.GetValue("Longitude", doc.GetValue("longitude", BsonValue.Create(0.0))).ToDouble();
            }

            var routes = doc.TryGetValue("routes_served", out var routesValue) && routesValue.IsBsonArray
                ? routesValue.AsBsonArray.Select(MapRoute).ToList()
                : new List<RoutesServed>();

            var agency = doc.GetValue("agency", BsonValue.Create(string.Empty)).ToString();

            return new BusStop
            {
                Id = id,
                Name = name,
                Agency = agency,
                Latitude = latitude,
                Longitude = longitude,
                DistanceM = sourceLatitude.HasValue && sourceLongitude.HasValue
                    ? CoordinateCalculator.GetDistanceInMeters(sourceLatitude.Value, sourceLongitude.Value, latitude, longitude)
                    : null,
                Routes = routes
            };
        }

        private static RoutesServed MapRoute(BsonValue route)
        {
            // Older loads stored routes_served as plain route id strings
            if (!route.IsBsonDocument)
            {
                return new RoutesServed { Id = route.ToString() };
            }

            var routeDoc = route.AsBsonDocument;
            return new RoutesServed
            {
                Id = routeDoc.GetValue("route_id", BsonValue.Create(string.Empty)).ToString(),
                ShortName = routeDoc.GetValue("route_short_name", BsonValue.Create(string.Empty)).ToString(),
                LongName = routeDoc.GetValue("route_long_name", BsonValue.Create(string.Empty)).ToString(),
                Color = routeDoc.GetValue("route_color", BsonValue.Create(string.Empty)).ToString()
            };
        }
    }
}
