using Busable.Business.Objects;

namespace Busable.Business.Interfaces
{
    /// <summary>
    /// Service responsible for operations around bus stops.
    /// </summary>
    public interface IBusStopsService
    {
        /// <summary>
        /// Get nearest bus stops.
        /// </summary>
        Task<NearestBusStopsResponse> GetNearestAsync(NearestBusStopsRequest request);
    }
}
