using static Busable.Common.Objects.Objects;

namespace Busable.Api.Models
{
    public class GetNearestStopRequest
    {
        public required Location Origin { get; set; }
        public int? MaxDistanceKm { get; set; }
    }
}
