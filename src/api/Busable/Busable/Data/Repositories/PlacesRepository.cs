using Busable.Business.Objects;
using Busable.Data.Interfaces;
using Busable.Data.Utilities;
using Microsoft.Extensions.Logging;
using MongoDB.Bson;
using MongoDB.Driver;

namespace Busable.Data.Repositories
{
    public class PlacesRepository : IPlacesRepository
    {
        private QueryHelper _queryHelper;
        private readonly IMongoDatabase _database;
        private readonly IMongoCollection<BsonDocument> _placesCollection;
        private readonly ILogger<PlacesRepository> _logger;

        public PlacesRepository(IMongoDatabase database, string placesCollectionName, ILogger<PlacesRepository> logger)
        {
            _database = database ?? throw new ArgumentNullException(nameof(database));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            if (string.IsNullOrWhiteSpace(placesCollectionName))
                throw new ArgumentException("Places collection name must be provided.", nameof(placesCollectionName));

            _placesCollection = _database.GetCollection<BsonDocument>(placesCollectionName);
            _queryHelper = new QueryHelper();
            _logger.LogInformation("PlacesRepository initialized with database '{DatabaseName}' and places collection: '{PlacesCollection}'", _database.DatabaseNamespace.DatabaseName, placesCollectionName);
        }

        public async Task<List<Place?>> GetNearestPlacesAsync(double latitude, double longitude, double maxDistanceM)
        {
            _logger.LogInformation("GetNearestPlacesAsync called. Lat: {Lat}, Lng: {Lng}, Radius: {Dist}m", latitude, longitude, maxDistanceM);
            var docs = await _queryHelper.GetNearestAsync(_placesCollection, latitude, longitude, maxDistanceM);
            _logger.LogInformation("Mongo Query returned {Count} raw documents for places query.", docs?.Count ?? 0);
            return docs?.Select(doc => MapDocument(doc, latitude, longitude)).ToList() ?? new List<Place?>();
        }

        private static Place MapDocument(BsonDocument doc, double sourceLatitude, double sourceLongitude)
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

            var category = doc.GetValue("category", BsonValue.Create(string.Empty)).ToString();
            var brand = doc.GetValue("brand", BsonValue.Create(BsonNull.Value)).IsBsonNull
                ? null
                : doc.GetValue("brand", BsonValue.Create(string.Empty)).ToString();
            var popularity = doc.GetValue("popularity_score", BsonValue.Create(0.0)).ToDouble();

            return new Place
            {
                Id = id,
                Name = name,
                Category = category,
                Brand = brand,
                Popularity_Score = popularity,
                Location = new GeoLocation
                {
                    Type = "Point",
                    Coordinates = new double[] { longitude, latitude }
                }
            };
        }
    }
}
