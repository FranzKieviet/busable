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
            var stop = await _repository.GetNearestAsync(request.Origin.Latitude, request.Origin.Longitude, request.MaxDistanceKm);

            return new NearestBusStopsResponse()
            {
                BusStop = stop
            };
        }
    }
}