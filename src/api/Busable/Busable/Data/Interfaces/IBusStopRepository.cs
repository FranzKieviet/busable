using Busable.Business.Objects;
using Busable.Business.Services;

namespace Busable.Data.Interfaces
{
    public interface IBusStopsRepository
    {
        Task<BusStop?> GetNearestAsync(double latitude, double longitude, double? maxDistanceKm);
    }
}
