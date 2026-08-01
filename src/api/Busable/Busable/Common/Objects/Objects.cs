namespace Busable.Common.Objects
{
    public class Objects
    {
        public class Location
        {
            public double Latitude { get; set; }
            public double Longitude { get; set; }
        }

        public class Error
        {
            public int Code { get; set; }
            public string Message { get; set; } = string.Empty;
        }
    }
}
