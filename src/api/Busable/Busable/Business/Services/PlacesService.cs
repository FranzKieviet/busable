using Busable.Business.Interfaces;
using Busable.Business.Objects;
using Busable.Data.Interfaces;
using Busable.Data.Objects;
using Busable.Data.Utilities;
using Microsoft.Extensions.Logging;

namespace Busable.Business.Services
{
    public class PlacesService : IPlacesService
    {
        private readonly IPlacesRepository _repository;
        private readonly IBusStopsRepository _busStopsRepository;
        private readonly ILogger<PlacesService> _logger;

        public PlacesService(IPlacesRepository repository, IBusStopsRepository busStopsRepository, ILogger<PlacesService> logger)
        {
            _repository = repository ?? throw new ArgumentNullException(nameof(repository));
            _busStopsRepository = busStopsRepository ?? throw new ArgumentNullException(nameof(busStopsRepository));
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

        public async Task<DownstreamPlacesResponse?> GetDownstreamPlacesAsync(DownstreamPlacesRequest request)
        {
            _logger.LogInformation("GetDownstreamPlacesAsync called with {@Request}", request);

            var route = await _busStopsRepository.GetDownstreamStopsAsync(request.RouteId, request.StopId);
            if (route == null)
            {
                _logger.LogInformation("GetDownstreamPlacesAsync found no route {RouteId}", request.RouteId);
                return null;
            }

            var response = new DownstreamPlacesResponse
            {
                RouteId = route.RouteId,
                RouteShortName = route.RouteShortName ?? string.Empty,
                OriginStopId = request.StopId
            };

            var downstream = route.DownstreamStops ?? new List<OrderedStopDbo>();
            var stopsById = (await _busStopsRepository.GetBusStopsByIdsAsync(downstream.Select(d => d.StopId)))
                .ToDictionary(s => s.Id);

            var originTimeSec = route.OriginCumulativeTimeSec ?? 0;
            var stopsFromOrigin = new Dictionary<string, int>();
            // Downstream stops start right after the origin, so the next stop is 1 stop away
            foreach (var (orderedStop, index) in downstream.Select((s, i) => (s, i)))
            {
                if (!stopsById.TryGetValue(orderedStop.StopId, out var stop))
                {
                    _logger.LogWarning("Downstream stop {StopId} on route {RouteId} not found in stops collection", orderedStop.StopId, route.RouteId);
                    continue;
                }

                response.Stops.Add(new DownstreamStopPlaces
                {
                    StopId = stop.Id,
                    StopName = stop.Name,
                    Latitude = stop.Latitude,
                    Longitude = stop.Longitude,
                    TravelTimeSec = orderedStop.TravelTimeSec - originTimeSec
                });
                stopsFromOrigin[stop.Id] = index + 1;
            }

            var places = await _repository.GetPlacesNearAnyAsync(response.Stops.Select(s => (s.Latitude, s.Longitude)), request.MaxDistanceM);

            // A place can be within range of several stops; list it once, under the stop it is closest to
            foreach (var place in places)
            {
                var placeLongitude = place.Location.Coordinates[0];
                var placeLatitude = place.Location.Coordinates[1];
                var closest = response.Stops
                    .Select(s => (Stop: s, DistanceM: CoordinateCalculator.GetDistanceInMeters(s.Latitude, s.Longitude, placeLatitude, placeLongitude)))
                    .MinBy(x => x.DistanceM);
                if (closest.Stop == null)
                {
                    continue;
                }

                closest.Stop.Places.Add(new DownstreamPlace
                {
                    Id = place.Id,
                    Name = place.Name,
                    Category = place.Category,
                    Brand = place.Brand,
                    Popularity_Score = place.Popularity_Score,
                    Location = place.Location,
                    ClosestStopId = closest.Stop.StopId,
                    ClosestStopName = closest.Stop.StopName,
                    StopsFromOrigin = stopsFromOrigin[closest.Stop.StopId],
                    DistanceToStopM = Math.Round(closest.DistanceM, 1)
                });
            }

            foreach (var stop in response.Stops)
            {
                stop.Places = stop.Places.OrderByDescending(p => p.Popularity_Score).ToList();
            }

            _logger.LogInformation("GetDownstreamPlacesAsync completed. Stops: {StopCount}, Places: {PlaceCount}", response.Stops.Count, places.Count);
            return response;
        }

    }
}