using static Busable.Common.Objects.Objects;

namespace Busable.Business.Objects
{
    public class NearestPlacesResponse
    {
        public Error? Error { get; set; }

        public List<Place?> Places { get; set; }
    }
}
