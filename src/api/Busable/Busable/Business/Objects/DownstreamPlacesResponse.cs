using static Busable.Common.Objects.Objects;

namespace Busable.Business.Objects
{
    public class DownstreamPlacesResponse
    {
        public Error? Error { get; set; }

        public string RouteId { get; set; } = string.Empty;

        public string RouteShortName { get; set; } = string.Empty;

        public string OriginStopId { get; set; } = string.Empty;

        // Downstream stops in route order, each with the places closest to it
        public List<DownstreamStopPlaces> Stops { get; set; } = new List<DownstreamStopPlaces>();
    }

    public class DownstreamStopPlaces
    {
        public string StopId { get; set; } = string.Empty;

        public string StopName { get; set; } = string.Empty;

        public double Latitude { get; set; }

        public double Longitude { get; set; }

        // Travel time in seconds from the origin stop to this stop
        public int TravelTimeSec { get; set; }

        public List<Place> Places { get; set; } = new List<Place>();
    }
}
