using Busable.Business.Interfaces;
using Busable.Business.Objects;
using Busable.Data.Interfaces;

namespace Busable.Business.Services
{
    public class BusStopsService : IBusStopsService
    {
        private readonly IBusStopsRepository _repository;

        public BusStopsService(IBusStopsRepository repository)
        {
            _repository = repository ?? throw new ArgumentNullException(nameof(repository));
        }

        public async Task<NearestBusStopsResponse> GetNearestAsync(Origin request)
        {
            var stops = await _repository.GetNearestBusStopAsync(request.Latitude, request.Longitude, request.MaxDistanceM);

            return new NearestBusStopsResponse()
            {
                BusStops = stops
            };
        }

        public async Task<NearestBusStopsByLineResponse> GetNearestByLineAsync(Origin request)
        {
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

            return new NearestBusStopsByLineResponse()
            {
                BusStops = filteredStops,
                UniqueRoutesList = uniqueRoutes.ToList()
            };
        }

        public async Task<DownstreamRouteResponse> GetDownstreamBusStops(Origin request)
        {
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

            return response;
        }

    }
}