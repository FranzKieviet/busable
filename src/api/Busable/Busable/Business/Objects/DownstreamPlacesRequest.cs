using System.ComponentModel.DataAnnotations;

namespace Busable.Business.Objects
{
    public class DownstreamPlacesRequest : IValidatableObject
    {
        // Stop the rider boards at
        public required string StopId { get; set; }

        // Route the rider takes from the stop
        public required string RouteId { get; set; }

        // Maximum distance in meters from each downstream stop to a place (default 250m)
        private int _maxDistanceM = 250;
        public int MaxDistanceM
        {
            get => _maxDistanceM;
            set => _maxDistanceM = (value == 0) ? 250 : value;
        }

        public IEnumerable<ValidationResult> Validate(ValidationContext validationContext)
        {
            var errors = new List<ValidationResult>();

            if (string.IsNullOrWhiteSpace(StopId))
                errors.Add(new ValidationResult("StopId is required.", new[] { nameof(StopId) }));

            if (string.IsNullOrWhiteSpace(RouteId))
                errors.Add(new ValidationResult("RouteId is required.", new[] { nameof(RouteId) }));

            if (MaxDistanceM <= 0)
                errors.Add(new ValidationResult("MaxDistanceM must be greater than 0.", new[] { nameof(MaxDistanceM) }));

            if (MaxDistanceM > 1000)
                errors.Add(new ValidationResult("MaxDistanceM must be less than or equal to 1000.", new[] { nameof(MaxDistanceM) }));

            return errors;
        }
    }
}
