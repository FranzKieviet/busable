using Busable.Business.Objects;
using Busable.Data.Interfaces;
using Busable.Data.Utilities;
using MongoDB.Bson;
using MongoDB.Driver;
using MongoDB.Driver.GeoJsonObjectModel;
using static Busable.Common.Objects.Objects;

namespace Busable.Data.Repositories
{
    public class BusStopRepository : IBusStopsRepository
    {
        private const string DefaultCollectionName = "stops";
        private readonly IMongoDatabase _database;
        private readonly IMongoCollection<BsonDocument> _collection;
        private const double DEFAULT_MAX_DISTANCE_M = 500;

        public BusStopRepository(IMongoDatabase database)
            : this(database, Environment.GetEnvironmentVariable("MONGO_COLLECTION_NAME") ?? DefaultCollectionName)
        {
        }

        public BusStopRepository(IMongoDatabase database, string collectionName)
        {
            _database = database ?? throw new ArgumentNullException(nameof(database));
            if (string.IsNullOrWhiteSpace(collectionName))
                throw new ArgumentException("Collection name must be provided.", nameof(collectionName));

            _collection = _database.GetCollection<BsonDocument>(collectionName);
        }

        public BusStopRepository(string connectionString, string databaseName, string? collectionName = null)
        {
            if (string.IsNullOrWhiteSpace(connectionString))
                throw new ArgumentException("MongoDB connection string must be provided.", nameof(connectionString));

            if (string.IsNullOrWhiteSpace(databaseName))
                throw new ArgumentException("MongoDB database name must be provided.", nameof(databaseName));

            var client = new MongoClient(connectionString);
            _database = client.GetDatabase(databaseName);
            var effectiveCollectionName = string.IsNullOrWhiteSpace(collectionName)
                ? Environment.GetEnvironmentVariable("MONGO_COLLECTION_NAME") ?? DefaultCollectionName
                : collectionName;

            _collection = _database.GetCollection<BsonDocument>(effectiveCollectionName);
        }

        public async Task<List<BusStop?>> GetNearestAsync(double latitude, double longitude, double? maxDistanceM)
        {
            var point = new GeoJsonPoint<GeoJson2DGeographicCoordinates>(
                new GeoJson2DGeographicCoordinates(longitude, latitude));

            var filter = Builders<BsonDocument>.Filter.Near("location", point, maxDistanceM.Value);

            var docs = await _collection.Find(filter).ToListAsync();
            return docs?.Select(doc => MapDocument(doc, latitude, longitude)).ToList() ?? new List<BusStop?>();
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
                Location = new Location
                {
                    Latitude = latitude,
                    Longitude = longitude
                },
                DistanceM = CoordinateCalculator.GetDistanceInMeters(sourceLatitude, sourceLongitude, latitude, longitude),
                Routes = routes
            };
        }
    }
}
