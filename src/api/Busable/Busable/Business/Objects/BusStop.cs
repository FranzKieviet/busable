namespace Busable.Business.Objects
{
    public class BusStop
    {
        public string Id { get; init; } = string.Empty;
        public string Name { get; init; } = string.Empty;
        public double Longitude { get; init; }
        public double Latitude { get; init; }
        public double? DistanceM { get; init; }
        public List<string> Routes { get; init; } = new List<string>();
    }
}
