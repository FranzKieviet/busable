namespace Busable.Business.Objects
{
    public class NearestBusStopsByLineResponse : NearestBusStopsResponse
    {

        public List<string> UniqueRoutes { get; set; }
    }
}
