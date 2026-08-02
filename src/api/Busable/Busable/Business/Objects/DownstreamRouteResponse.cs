namespace Busable.Business.Objects
{
    public class DownstreamRouteResponse
    {
        public Dictionary<string, string> RouteNames { get; set; } = new Dictionary<string, string>();

        public Dictionary<string, List<OrderedStop>> DownstreamStops { get; set; } = new Dictionary<string, List<OrderedStop>>();
    }
    public class OrderedStop
    {
        public string StopId { get; set; }

        public int TravelTimeSec { get; set; }
    }
}
