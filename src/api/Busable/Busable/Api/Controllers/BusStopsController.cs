using Busable.Business.Interfaces;
using Busable.Business.Objects;
using Microsoft.AspNetCore.Mvc;
using System.ComponentModel.DataAnnotations;

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
        [Route("bus-stops/nearest-stops")]
        public async Task<ActionResult<NearestBusStopsResponse>> GetNearestBusStops([FromQuery] double longitude, [FromQuery] double latitude, [FromQuery] int distance)
        {
            var nearestBusStopsRequest = new Origin
            {
                Longitude = longitude,
                Latitude = latitude,
                MaxDistanceM = distance
            };

            // Explicitly run data annotations validation since the request is created manually
            var validationResults = new List<ValidationResult>();
            var context = new ValidationContext(nearestBusStopsRequest);
            if (!Validator.TryValidateObject(nearestBusStopsRequest, context, validationResults, validateAllProperties: true))
            {
                // Return 400 with validation error messages
                var errors = validationResults.Select(r => new { r.ErrorMessage, Members = r.MemberNames.ToArray() });
                return BadRequest(new { Errors = errors });
            }

            var response = await _service.GetNearestAsync(nearestBusStopsRequest);
            return Ok(response);
        }

        [HttpGet]
        [Route("bus-stops/nearest-stops-by-line")]
        public async Task<ActionResult<NearestBusStopsResponse>> GetNearestBusStopsByLine([FromQuery] double longitude, [FromQuery] double latitude, [FromQuery] int distance)
        {
            var nearestBusStopsRequest = new Origin
            {
                Longitude = longitude,
                Latitude = latitude,
                MaxDistanceM = distance
            };

            // Explicitly run data annotations validation since the request is created manually
            var validationResults = new List<ValidationResult>();
            var context = new ValidationContext(nearestBusStopsRequest);
            if (!Validator.TryValidateObject(nearestBusStopsRequest, context, validationResults, validateAllProperties: true))
            {
                // Return 400 with validation error messages
                var errors = validationResults.Select(r => new { r.ErrorMessage, Members = r.MemberNames.ToArray() });
                return BadRequest(new { Errors = errors });
            }

            var response = await _service.GetNearestByLineAsync(nearestBusStopsRequest);
            return Ok(response);
        }


        [HttpGet]
        [Route("bus-stops/downstream-stops-by-line")]
        public async Task<ActionResult<NearestBusStopsResponse>> GetDownstreamBusStopsByLine([FromQuery] double longitude, [FromQuery] double latitude, [FromQuery] int distance)
        {

            var nearestBusStopsRequest = new Origin
            {
                Longitude = longitude,
                Latitude = latitude,
                MaxDistanceM = distance
            };

            // Explicitly run data annotations validation since the request is created manually
            var validationResults = new List<ValidationResult>();
            var context = new ValidationContext(nearestBusStopsRequest);
            if (!Validator.TryValidateObject(nearestBusStopsRequest, context, validationResults, validateAllProperties: true))
            {
                // Return 400 with validation error messages
                var errors = validationResults.Select(r => new { r.ErrorMessage, Members = r.MemberNames.ToArray() });
                return BadRequest(new { Errors = errors });
            }

            var response = await _service.GetDownstreamBusStops(nearestBusStopsRequest);
            return Ok(response);
        }
    }
}
