using Busable.Business.Interfaces;
using Busable.Business.Objects;
using Busable.Data.Interfaces;

namespace Busable.Business.Services
{
    public class PlacesService : IPlacesService
    {
        private readonly IPlacesRepository _repository;

        public PlacesService(IPlacesRepository repository)
        {
            _repository = repository ?? throw new ArgumentNullException(nameof(repository));
        }

        public async Task<NearestPlacesResponse> GetNearestAsync(Origin request)
        {
            var places = await _repository.GetNearestPlacesAsync(request.Latitude, request.Longitude, request.MaxDistanceM);

            return new NearestPlacesResponse()
            {
                Places = places
            };
        }

    }
}