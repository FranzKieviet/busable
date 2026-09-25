namespace Busable.Business.Objects
{
    public class BusStop
    {
        public string Id { get; init; } = string.Empty;
        public string Name { get; init; } = string.Empty;
        public string Agency { get; init; } = string.Empty;
        public double Longitude { get; init; }
        public double Latitude { get; init; }
        public double? DistanceM { get; init; }
        public List<RoutesServed> Routes { get; init; } = new List<RoutesServed>();
    }

    public class RoutesServed
    {
        public string Id { get; init; } = string.Empty;
        public string LongName { get; init; } = string.Empty;
        public string ShortName { get; init; } = string.Empty;
        public string Color { get; init; } = string.Empty;
    }

}
