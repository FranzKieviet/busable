using Busable.Api.Models;
using Busable.Business.Interfaces;
using Busable.Business.Objects;
using Microsoft.AspNetCore.Mvc;
using static Busable.Common.Objects.Objects;

namespace Busable.Api.Controllers
{
    [ApiController]
    public class BusStopsController : ControllerBase
    {

        private readonly IBusStopsService _service;

        public BusStopsController(IBusStopsService service)
        {
            _service = service ?? throw new ArgumentNullException(nameof(service));
        }

        /***
         Input: Location object 
         Response: List of bus stops sorted by distance from the input location
            //TODO Write better docs here :)
         ***/

        [HttpGet]
        [Route("bus-stops/nearest-stop")]
        public async Task<NearestBusStopsResponse> Get() //GetNearestStopRequest request)
        {

            var newRequest = new GetNearestStopRequest
            {
                Origin = new Location { Longitude = -122.25902, Latitude = 37.86905 }
            };
            var nearestBusStopsRequest = createRequest(newRequest);
            return await _service.GetNearestAsync(nearestBusStopsRequest);
        }

        private NearestBusStopsRequest createRequest(GetNearestStopRequest request)
        {
            return new NearestBusStopsRequest
            {
                Origin = request.Origin,
                MaxDistanceKm = request.MaxDistanceKm
            };
        }
    }
}
