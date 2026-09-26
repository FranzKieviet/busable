using Busable.Business.Interfaces;
using Busable.Business.Objects;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using System.ComponentModel.DataAnnotations;

namespace Busable.Api.Controllers
{
    [ApiController]
    public class PlacesController : ControllerBase
    {

        private readonly IPlacesService _service;
        private readonly ILogger<PlacesController> _logger;

        public PlacesController(IPlacesService service, ILogger<PlacesController> logger)
        {
            _service = service ?? throw new ArgumentNullException(nameof(service));
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _logger.LogInformation("PlacesController initialized");
        }

        /***
         Input: Location object 
         Response: List of bus stops sorted by distance from the input location
            //TODO Write better docs here :)
         ***/

        [HttpGet]
        [Route("places/nearest")]
        public async Task<ActionResult<NearestBusStopsResponse>> SearchNearestPlaces([FromQuery] double longitude, [FromQuery] double latitude, [FromQuery] int distance)
        {
            var nearestPlaceRequest = new Origin
            {
                Longitude = longitude,
                Latitude = latitude,
                MaxDistanceM = distance
            };

            // Explicitly run data annotations validation since the request is created manually
            var validationResults = new List<ValidationResult>();
            var context = new ValidationContext(nearestPlaceRequest);
            if (!Validator.TryValidateObject(nearestPlaceRequest, context, validationResults, validateAllProperties: true))
            {
                _logger.LogWarning("Validation failed for SearchNearestPlaces request: {@Request} - Errors: {@Errors}", nearestPlaceRequest, validationResults.Select(r => r.ErrorMessage));
                // Return 400 with validation error messages
                var errors = validationResults.Select(r => new { r.ErrorMessage, Members = r.MemberNames.ToArray() });
                return BadRequest(new { Errors = errors });
            }

            _logger.LogInformation("SearchNearestPlaces called with {@Request}", nearestPlaceRequest);
            var response = await _service.GetNearestAsync(nearestPlaceRequest);
            _logger.LogInformation("SearchNearestPlaces completed. Returned {Count} places", response?.Places?.Count ?? 0);
            return Ok(response);
        }

        /***
         Input: Stop id and route id the rider boards, and an optional distance (meters) to search around each stop
         Response: The stops within 15 minutes downstream of the given stop on the route, in route order,
            each with the places closest to it, sorted by popularity
         ***/

        [HttpGet]
        [Route("places/downstream")]
        public async Task<ActionResult<DownstreamPlacesResponse>> GetDownstreamPlaces([FromQuery] string stopId, [FromQuery] string routeId, [FromQuery] int distance)
        {
            var downstreamPlacesRequest = new DownstreamPlacesRequest
            {
                StopId = stopId,
                RouteId = routeId,
                MaxDistanceM = distance
            };

            // Explicitly run data annotations validation since the request is created manually
            var validationResults = new List<ValidationResult>();
            var context = new ValidationContext(downstreamPlacesRequest);
            if (!Validator.TryValidateObject(downstreamPlacesRequest, context, validationResults, validateAllProperties: true))
            {
                _logger.LogWarning("Validation failed for GetDownstreamPlaces request: {@Request} - Errors: {@Errors}", downstreamPlacesRequest, validationResults.Select(r => r.ErrorMessage));
                // Return 400 with validation error messages
                var errors = validationResults.Select(r => new { r.ErrorMessage, Members = r.MemberNames.ToArray() });
                return BadRequest(new { Errors = errors });
            }

            _logger.LogInformation("GetDownstreamPlaces called with {@Request}", downstreamPlacesRequest);
            var response = await _service.GetDownstreamPlacesAsync(downstreamPlacesRequest);
            if (response == null)
            {
                return NotFound(new { Errors = new[] { new { ErrorMessage = $"Route '{routeId}' was not found." } } });
            }

            _logger.LogInformation("GetDownstreamPlaces completed. Returned {Count} downstream stops", response.Stops.Count);
            return Ok(response);
        }
    }
}
