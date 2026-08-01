using static Busable.Common.Objects.Objects;

namespace Busable.Business.Objects
{
    public class BusStop
    {
        public string Id { get; init; } = string.Empty;
        public string Name { get; init; } = string.Empty;
        public Location Location { get; init; }
        public double? DistanceM { get; init; }
    }
}
