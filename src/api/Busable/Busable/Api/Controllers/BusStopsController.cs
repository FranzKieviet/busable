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
        private readonly ILogger<BusStopsController> _logger;

        public BusStopsController(IBusStopsService service, ILogger<BusStopsController> logger)
        {
            _service = service ?? throw new ArgumentNullException(nameof(service));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _logger.LogInformation("BusStopsController initialized");
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
                _logger.LogWarning("Validation failed for GetNearestBusStops request: {@Request} - Errors: {@Errors}", nearestBusStopsRequest, validationResults.Select(r => r.ErrorMessage));
                // Return 400 with validation error messages
                var errors = validationResults.Select(r => new { r.ErrorMessage, Members = r.MemberNames.ToArray() });
                return BadRequest(new { Errors = errors });
            }

            _logger.LogInformation("GetNearestBusStops called with {@Request}", nearestBusStopsRequest);
            var response = await _service.GetNearestAsync(nearestBusStopsRequest);
            _logger.LogInformation("GetNearestBusStops completed. Returned {Count} stops", response?.BusStops?.Count ?? 0);
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
                _logger.LogWarning("Validation failed for GetNearestBusStopsByLine request: {@Request} - Errors: {@Errors}", nearestBusStopsRequest, validationResults.Select(r => r.ErrorMessage));
                // Return 400 with validation error messages
                var errors = validationResults.Select(r => new { r.ErrorMessage, Members = r.MemberNames.ToArray() });
                return BadRequest(new { Errors = errors });
            }

            _logger.LogInformation("GetNearestBusStopsByLine called with {@Request}", nearestBusStopsRequest);
            var response = await _service.GetNearestByLineAsync(nearestBusStopsRequest);
            _logger.LogInformation("GetNearestBusStopsByLine completed. Returned {Count} stops and {Routes} unique routes", response?.BusStops?.Count ?? 0, response?.UniqueRoutesList?.Count ?? 0);
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
                _logger.LogWarning("Validation failed for GetDownstreamBusStopsByLine request: {@Request} - Errors: {@Errors}", nearestBusStopsRequest, validationResults.Select(r => r.ErrorMessage));
                // Return 400 with validation error messages
                var errors = validationResults.Select(r => new { r.ErrorMessage, Members = r.MemberNames.ToArray() });
                return BadRequest(new { Errors = errors });
            }

            _logger.LogInformation("GetDownstreamBusStopsByLine called with {@Request}", nearestBusStopsRequest);
            var response = await _service.GetDownstreamBusStops(nearestBusStopsRequest);
            _logger.LogInformation("GetDownstreamBusStopsByLine completed. Routes found: {RoutesCount}", response?.DownstreamStops?.Count ?? 0);
            return Ok(response);
        }
    }
}
