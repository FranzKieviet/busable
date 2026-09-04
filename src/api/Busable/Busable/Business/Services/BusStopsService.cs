using Busable.Business.Interfaces;
using Busable.Business.Objects;
using Busable.Data.Interfaces;
using Microsoft.Extensions.Logging;

namespace Busable.Business.Services
{
    public class BusStopsService : IBusStopsService
    {
        private readonly IBusStopsRepository _repository;
        private readonly ILogger<BusStopsService> _logger;

        public BusStopsService(IBusStopsRepository repository, ILogger<BusStopsService> logger)
        {
            _repository = repository ?? throw new ArgumentNullException(nameof(repository));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _logger.LogInformation("BusStopsService initialized");
        }

        public async Task<NearestBusStopsResponse> GetNearestAsync(Origin request)
        {
            _logger.LogInformation("GetNearestAsync called with {@Request}", request);
            var stops = await _repository.GetNearestBusStopAsync(request.Latitude, request.Longitude, request.MaxDistanceM);
            _logger.LogInformation("GetNearestAsync retrieved {Count} stops", stops?.Count ?? 0);

            return new NearestBusStopsResponse()
            {
                BusStops = stops
            };
        }

        public async Task<NearestBusStopsByLineResponse> GetNearestByLineAsync(Origin request)
        {
            _logger.LogInformation("GetNearestByLineAsync called with {@Request}", request);
            var stops = await _repository.GetNearestBusStopAsync(request.Latitude, request.Longitude, request.MaxDistanceM);

            HashSet<string> uniqueRoutes = new HashSet<string>();
            HashSet<string> uniqueStops = new HashSet<string>();
            var filteredStops = new List<BusStop?>();

            foreach (var stop in stops)
            {
                //Since the list of stops is sorted by distance, we can just add the first stop for each unique route
                if (stop?.Routes != null)
                {
                    foreach (var route in stop.Routes)
                    {
                        if (!uniqueRoutes.Contains(route))
                        {
                            uniqueRoutes.Add(route);
                            if (!uniqueStops.Contains(stop.Id))
                            {
                                uniqueStops.Add(stop.Id);
                                filteredStops.Add(stop);
                            }
                        }
                    }
                }
            }

            await _repository.GetDownstreamStopsAsync("ac-transit_route_6_1", "ac-transit_stop_5598");

            var response = new NearestBusStopsByLineResponse()
            {
                BusStops = filteredStops,
                UniqueRoutesList = uniqueRoutes.ToList()
            };

            _logger.LogInformation("GetNearestByLineAsync completed. Filtered stops: {Count}, Unique routes: {Routes}", response.BusStops?.Count ?? 0, response.UniqueRoutesList?.Count ?? 0);

            return response;
        }

        public async Task<DownstreamRouteResponse> GetDownstreamBusStops(Origin request)
        {
            _logger.LogInformation("GetDownstreamBusStops called with {@Request}", request);
            var getNearestByLineResponse = await GetNearestByLineAsync(request);
            var uniqueStops = getNearestByLineResponse.BusStops;
            var stops = await _repository.GetNearestBusStopAsync(request.Latitude, request.Longitude, request.MaxDistanceM);

            HashSet<string> routesSeen = new HashSet<string>();
            var response = new DownstreamRouteResponse();

            foreach (var stop in uniqueStops)
            {
                if (stop != null && stop.Routes != null)
                {
                    foreach (var route in stop.Routes)
                    {
                        if (!routesSeen.Contains(route))
                        {
                            routesSeen.Add(route);
                            var downstreamStopsDbo = await _repository.GetDownstreamStopsAsync(route, stop.Id);
                            var mappedDownstream = downstreamStopsDbo?.DownstreamStops?
                                .Select(d => new OrderedStop { StopId = d.StopId, TravelTimeSec = d.TravelTimeSec })
                                .ToList() ?? new List<OrderedStop>();

                            response.DownstreamStops[route] = mappedDownstream;
                            response.RouteNames[route] = downstreamStopsDbo?.RouteShortName ?? string.Empty;
                        }

                    }
                }
            }

            _logger.LogInformation("GetDownstreamBusStops completed. Routes included: {Count}", response.DownstreamStops.Count);
            return response;
        }

    }
}