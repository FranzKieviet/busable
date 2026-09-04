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
    }
}
