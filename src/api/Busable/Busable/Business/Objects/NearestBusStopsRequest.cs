using System.ComponentModel.DataAnnotations;
using static Busable.Common.Objects.Objects;

namespace Busable.Business.Objects
{
    public class NearestBusStopsRequest : IValidatableObject
    {
        public required Location Origin { get; set; }

        public int MaxDistanceM { get; set; }


        public IEnumerable<ValidationResult> Validate(ValidationContext validationContext)
        {
            var errors = new List<ValidationResult>();

            //Check if the given location is roughly in California
            if (!IsInCaliforniaBoundingBox(Origin.Latitude, Origin.Longitude))
                errors.Add(new ValidationResult("The given location is not in California.", new[] { nameof(Origin) }));

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
