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
        private readonly IMongoCollection<BsonDocument> _stopsCollection;
        private readonly IMongoCollection<BsonDocument> _routesCollection;
        private const int MAX_TIME = 900; //15 mins in seconds
        private readonly ILogger<BusStopRepository> _logger;

        public BusStopRepository(IMongoDatabase database, string stopsCollectionName, string routesCollectionName, ILogger<BusStopRepository> logger)
        {
            _database = database ?? throw new ArgumentNullException(nameof(database));
            if (string.IsNullOrWhiteSpace(stopsCollectionName))
                throw new ArgumentException("Stops collection name must be provided.", nameof(stopsCollectionName));
            if (string.IsNullOrWhiteSpace(routesCollectionName))
                throw new ArgumentException("Routes collection name must be provided.", nameof(routesCollectionName));
            _stopsCollection = _database.GetCollection<BsonDocument>(stopsCollectionName);
            _routesCollection = _database.GetCollection<BsonDocument>(routesCollectionName);
            _queryHelper = new QueryHelper();
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));

            _logger.LogInformation("BusStopRepository initialized with database '{DatabaseName}' and stops collection: '{StopsCollection}' and routes collection: '{RoutesCollection}'", _database.DatabaseNamespace.DatabaseName, stopsCollectionName, routesCollectionName);
        }

        public async Task<List<BusStop?>> GetNearestBusStopAsync(double latitude, double longitude, double maxDistanceM)
        {
            _logger.LogInformation("GetNearestBusStopAsync called. Lat: {Lat}, Lng: {Lng}, Radius: {Dist}m", latitude, longitude, maxDistanceM);
            var docs = await _queryHelper.GetNearestAsync(_stopsCollection, latitude, longitude, maxDistanceM);
            _logger.LogInformation("Mongo Query returned {Count} raw documents.", docs?.Count ?? 0);
            return docs?.Select(doc => MapDocument(doc, latitude, longitude)).ToList() ?? new List<BusStop?>();
        }

        public async Task<DownstreamRouteDbo> GetDownstreamStopsAsync(string targetRouteId, string originStopId)
        {
            var pipeline = new BsonDocument[]
            {
                // Stage 1: Match route ID
                new BsonDocument("$match",
                    new BsonDocument("_id", targetRouteId)),

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
                        { "_id", 1 },
                        { "route_short_name", 1 },
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
            var result = await _routesCollection.Aggregate<DownstreamRouteDbo>(pipeline).FirstOrDefaultAsync();
            return result;
        }

        private static BusStop MapDocument(BsonDocument doc, double sourceLatitude, double sourceLongitude)
        {
            var id = doc.GetValue("_id", BsonValue.Create(string.Empty)).ToString();
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
                ? routesValue.AsBsonArray.Select(r => r.ToString()).ToList()
                : new List<string>();

            return new BusStop
            {
                Id = id,
                Name = name,
                Latitude = latitude,
                Longitude = longitude,
                DistanceM = CoordinateCalculator.GetDistanceInMeters(sourceLatitude, sourceLongitude, latitude, longitude),
                Routes = routes
            };
        }
    }
}
