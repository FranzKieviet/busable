namespace Busable.Data.Objects
{
    /// <summary>
    /// Database object representing a bus stop.
    /// </summary>
    public class BusStopDbo
    {
        /// <summary>Primary key.</summary>
        public Guid Id { get; set; }

        /// <summary>External or provider-specific stop code/identifier.</summary>
        public string StopCode { get; set; } = string.Empty;

        /// <summary>Human readable name of the stop.</summary>
        public string Name { get; set; } = string.Empty;

        /// <summary>Latitude in decimal degrees.</summary>
        public double Latitude { get; set; }

        /// <summary>Longitude in decimal degrees.</summary>
        public double Longitude { get; set; }

        /// <summary>Optional address or description.</summary>
        public string Address { get; set; } = string.Empty;

        /// <summary>City or locality.</summary>
        public string City { get; set; } = string.Empty;

        /// <summary>Fare zone or area.</summary>
        public string Zone { get; set; } = string.Empty;

        /// <summary>Whether the stop is currently active/serviced.</summary>
        public bool IsActive { get; set; } = true;

        /// <summary>UTC timestamp when the record was created.</summary>
        public DateTimeOffset CreatedAt { get; set; }

        /// <summary>UTC timestamp of last update.</summary>
        public DateTimeOffset UpdatedAt { get; set; }

        /// <summary>List of route identifiers that serve this stop.</summary>
        public List<string> Routes { get; set; } = new();
    }
}
