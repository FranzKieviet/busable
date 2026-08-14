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
    }
}
