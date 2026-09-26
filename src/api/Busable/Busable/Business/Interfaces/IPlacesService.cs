using Busable.Business.Objects;

namespace Busable.Business.Interfaces
{
    /// <summary>
    /// Service responsible for operations around places
    /// </summary>
    public interface IPlacesService
    {
        /// <summary>
        /// Get nearest places of interest near a location .
        /// </summary>
        Task<NearestPlacesResponse> GetNearestAsync(Origin request);

        /// <summary>
        /// Get places near the stops downstream of a stop on a route, grouped by the closest downstream stop.
        /// Returns null if the route does not exist.
        /// </summary>
        Task<DownstreamPlacesResponse?> GetDownstreamPlacesAsync(DownstreamPlacesRequest request);
    }
}
