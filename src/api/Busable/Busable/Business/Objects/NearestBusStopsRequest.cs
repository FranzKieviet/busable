using System.ComponentModel.DataAnnotations;
using static Busable.Common.Objects.Objects;

namespace Busable.Business.Objects
{
    public class NearestBusStopsRequest : IValidatableObject
    {
        public required Location Origin { get; set; }

        public int? MaxDistanceKm { get; set; } = 1;


        public IEnumerable<ValidationResult> Validate(ValidationContext validationContext)
        {
            var errors = new List<ValidationResult>();

            //Check if the given location is roughly in california
            if (!IsInCaliforniaBoundingBox(Origin.Latitude, Origin.Longitude))
                errors.Add(new ValidationResult("The given location is not in California.", new[] { nameof(Origin) }));

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
