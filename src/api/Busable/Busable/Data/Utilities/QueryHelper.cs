using MongoDB.Driver;
using MongoDB.Driver.GeoJsonObjectModel;

namespace Busable.Data.Utilities
{
    public class QueryHelper
    {
        public async Task<List<T>> GetNearestAsync<T>(IMongoCollection<T> collection, double latitude, double longitude, double maxDistanceM)
        {
            if (collection == null) throw new ArgumentNullException(nameof(collection));

            var point = new GeoJsonPoint<GeoJson2DGeographicCoordinates>(
                new GeoJson2DGeographicCoordinates(longitude, latitude));

            FilterDefinition<T> filter;
            filter = Builders<T>.Filter.Near("location", point, maxDistanceM);

            return await collection.Find(filter).ToListAsync();
        }

    }
}
