using Busable.Business.Objects;

namespace Busable.Data.Interfaces
{
    public interface IPlacesRepository
    {
        Task<List<Place?>> GetNearestPlacesAsync(double latitude, double longitude, double maxDistanceM);
        Task<List<Place>> GetPlacesNearAnyAsync(IEnumerable<(double Latitude, double Longitude)> points, double maxDistanceM);
    }
}
