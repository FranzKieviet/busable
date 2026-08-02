using MongoDB.Bson.Serialization.Attributes;

namespace Busable.Data.Objects
{

    public class DownstreamRouteDbo
    {
        [BsonId]
        public string Id { get; set; }

        [BsonElement("route_short_name")]
        public string RouteShortName { get; set; }

        [BsonElement("downstream_stops")]
        public List<OrderedStopDbo> DownstreamStops { get; set; }
    }

    public class OrderedStopDbo
    {
        [BsonElement("stop_id")]
        public string StopId { get; set; }

        [BsonElement("sequence")]
        public int Sequence { get; set; }

        [BsonElement("cumulative_time_sec")]
        public int TravelTimeSec { get; set; }
    }
}
