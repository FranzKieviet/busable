using Busable.Business.Objects;

namespace Busable.Data.Interfaces
{
    public interface IBusStopsRepository
    {
        Task<List<BusStop?>> GetNearestAsync(double latitude, double longitude, double? maxDistanceM);
    }
}
