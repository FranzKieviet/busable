namespace Busable.Business.Objects
{
    public class Place
    {
        public string? Id { get; set; }

        public string Name { get; set; } = string.Empty;

        public string Category { get; set; } = string.Empty;

        public string? Brand { get; set; }

        public double Popularity_Score { get; set; }

        public GeoLocation Location { get; set; } = new GeoLocation();
    }

    public class GeoLocation
    {
        public string Type { get; set; } = "Point";

        // [longitude, latitude]
        public double[] Coordinates { get; set; } = Array.Empty<double>();
    }
}
