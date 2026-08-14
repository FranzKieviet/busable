using System.ComponentModel.DataAnnotations;

namespace Busable.Business.Objects
{
    public class Origin : IValidatableObject
    {
        // Latitude in decimal degrees
        public required double Latitude { get; set; }

        // Longitude in decimal degrees
        public required double Longitude { get; set; }

        // Maximum search distance in meters (default 500m)
        private int _maxDistanceM = 500;
        public int MaxDistanceM
        {
            get => _maxDistanceM;
            set => _maxDistanceM = (value == 0) ? 500 : value;
        }

        public IEnumerable<ValidationResult> Validate(ValidationContext validationContext)
        {
            var errors = new List<ValidationResult>();

            // Check if the given location is roughly in California
            if (!IsInCaliforniaBoundingBox(Latitude, Longitude))
                errors.Add(new ValidationResult("The given location is not in California.", new[] { nameof(Latitude), nameof(Longitude) }));

            if (MaxDistanceM <= 0)
                errors.Add(new ValidationResult("MaxDistanceM must be greater than 0.", new[] { nameof(MaxDistanceM) }));

            if (MaxDistanceM > 5000)
                errors.Add(new ValidationResult("MaxDistanceM must be less than or equal to 5000.", new[] { nameof(MaxDistanceM) }));

            return errors;
        }

        private bool IsInCaliforniaBoundingBox(double latitude, double longitude)
        {
            // California's rough lat/long box limits
            return (latitude >= 32.5 && latitude <= 42.0) &&
                   (longitude >= -124.5 && longitude <= -114.1);
        }
    }
}
