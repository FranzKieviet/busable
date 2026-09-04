using Busable.Business.Interfaces;
using Busable.Business.Objects;
using Busable.Data.Interfaces;
using Microsoft.Extensions.Logging;

namespace Busable.Business.Services
{
    public class PlacesService : IPlacesService
    {
        private readonly IPlacesRepository _repository;
        private readonly ILogger<PlacesService> _logger;

        public PlacesService(IPlacesRepository repository, ILogger<PlacesService> logger)
        {
            _repository = repository ?? throw new ArgumentNullException(nameof(repository));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _logger.LogInformation("PlacesService initialized");
        }

        public async Task<NearestPlacesResponse> GetNearestAsync(Origin request)
        {
            _logger.LogInformation("GetNearestAsync called for places with {@Request}", request);
            var places = await _repository.GetNearestPlacesAsync(request.Latitude, request.Longitude, request.MaxDistanceM);
            _logger.LogInformation("GetNearestAsync retrieved {Count} places", places?.Count ?? 0);

            return new NearestPlacesResponse()
            {
                Places = places
            };
        }

    }
}