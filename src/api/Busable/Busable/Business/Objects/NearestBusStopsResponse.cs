using static Busable.Common.Objects.Objects;

namespace Busable.Business.Objects
{
    public class NearestBusStopsResponse
    {
        public Error? Error { get; set; }

        public List<BusStop?> BusStops { get; set; }
    }
}
