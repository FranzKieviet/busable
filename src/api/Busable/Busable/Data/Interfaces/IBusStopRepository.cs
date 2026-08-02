using Busable.Business.Objects;
using Busable.Data.Objects;

namespace Busable.Data.Interfaces
{
    public interface IBusStopsRepository
    {
        Task<List<BusStop?>> GetNearestAsync(double latitude, double longitude, double? maxDistanceM);
        Task<DownstreamRouteDbo> GetDownstreamStopsAsync(string targetRouteId, string originStopId);
    }
}
