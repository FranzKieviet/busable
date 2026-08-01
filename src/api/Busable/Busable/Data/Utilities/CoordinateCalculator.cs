namespace Busable.Data.Utilities
{
    public static class CoordinateCalculator
    {
        // Mean radius of the Earth in meters
        private const double EarthRadiusMeters = 6371000.0;

        public static double GetDistanceInMeters(double lat1, double lon1, double lat2, double lon2)
        {
            // 1. Convert degrees to radians
            double dLat = (lat2 - lat1) * (Math.PI / 180.0);
            double dLon = (lon2 - lon1) * (Math.PI / 180.0);

            double rLat1 = lat1 * (Math.PI / 180.0);
            double rLat2 = lat2 * (Math.PI / 180.0);

            // 2. Apply the mathematical Haversine formula
            double a = Math.Sin(dLat / 2) * Math.Sin(dLat / 2) +
                       Math.Cos(rLat1) * Math.Cos(rLat2) *
                       Math.Sin(dLon / 2) * Math.Sin(dLon / 2);

            double c = 2 * Math.Atan2(Math.Sqrt(a), Math.Sqrt(1 - a));

            // 3. Calculate final distance in meters
            return EarthRadiusMeters * c;
        }
    }
}
