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


        public async Task<NearestBusStopsResponse> GetNearestAsync(NearestBusStopsRequest request)
        {
            var stops = await _repository.GetNearestAsync(request.Origin.Latitude, request.Origin.Longitude, request.MaxDistanceM);

            return new NearestBusStopsResponse()
            {
                BusStops = stops
            };
        }

        public async Task<NearestBusStopsByLineResponse> GetNearestByLineAsync(NearestBusStopsRequest request)
        {
            var stops = await _repository.GetNearestAsync(request.Origin.Latitude, request.Origin.Longitude, request.MaxDistanceM);

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

            return new NearestBusStopsByLineResponse()
            {
                BusStops = filteredStops,
                UniqueRoutes = uniqueRoutes.ToList()
            };
        }
    }
}