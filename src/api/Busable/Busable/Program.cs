using Busable.Business.Interfaces;
using Busable.Business.Services;
using Busable.Data.Interfaces;
using Busable.Data.Repositories;
using MongoDB.Driver;
using System.Text.RegularExpressions;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();

// Determine the MongoDB connection string. Priority:
// 1. Configuration (appsettings) Mongo:ConnectionString
// 2. MONGO_CONNECTION env var (full connection string)
// 3. MONGO_USER, MONGO_PASSWORD, MONGO_HOST env vars (built URI)
// 4. Fallback to localhost host without auth for local development
var mongoConnectionString = builder.Configuration.GetConnectionString("MongoDb")
    ?? builder.Configuration["Mongo:ConnectionString"]
    ?? Environment.GetEnvironmentVariable("MONGO_CONNECTION")
    ?? "mongodb://busable-local-mongo:27017";

mongoConnectionString = mongoConnectionString?.Trim() ?? throw new InvalidOperationException("Mongo connection string is null or empty.");

var mongoDatabaseName = builder.Configuration.GetValue<string>("Mongo:DatabaseName")
    ?? Environment.GetEnvironmentVariable("MONGO_DATABASE_NAME")
    ?? "busable_feat_routing";

var settings = MongoClientSettings.FromConnectionString(mongoConnectionString);
var client = new MongoClient(settings);

builder.Services.AddSingleton<IMongoClient>(_ => new MongoClient(mongoConnectionString));
builder.Services.AddSingleton<IMongoDatabase>(sp => sp.GetRequiredService<IMongoClient>().GetDatabase(mongoDatabaseName));
// Resolve collection name from environment variable if provided, otherwise use the
// routing dataset collection used in your environment.
var stopsCollectionName = Environment.GetEnvironmentVariable("MONGO__STOPS_COLLECTION_NAME")
    ?? "stops_ac-transit_20260816_213922";
var routesCollectionName = Environment.GetEnvironmentVariable("MONGO__ROUTES_COLLECTION_NAME")
    ?? "routes_ac-transit_20260816_213922";
var placesCollectionName = Environment.GetEnvironmentVariable("MONGO__PLACES_COLLECTION_NAME")
    ?? "places_20260813_193405";


builder.Services.AddSingleton<IBusStopsRepository>(sp =>
    new BusStopRepository(
        sp.GetRequiredService<IMongoDatabase>(),
        stopsCollectionName,
        routesCollectionName,
        sp.GetRequiredService<ILogger<BusStopRepository>>()
    ));
builder.Services.AddSingleton<IPlacesRepository>(sp =>
    new PlacesRepository(sp.GetRequiredService<IMongoDatabase>(), placesCollectionName, sp.GetRequiredService<ILogger<PlacesRepository>>()));
builder.Services.AddScoped<IBusStopsService, BusStopsService>();
builder.Services.AddScoped<IPlacesService, PlacesService>();

// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();

builder.Services.AddHealthChecks();

var app = builder.Build();

app.MapHealthChecks("/health");

static string? BuildMongoConnectionStringFromEnv()
{
    var envUser = Environment.GetEnvironmentVariable("MONGO_USER");
    var envPass = Environment.GetEnvironmentVariable("MONGO_PASSWORD");
    var envHost = Environment.GetEnvironmentVariable("MONGO_HOST");
    if (!string.IsNullOrWhiteSpace(envUser) && !string.IsNullOrWhiteSpace(envPass) && !string.IsNullOrWhiteSpace(envHost))
    {
        return $"mongodb://{Uri.EscapeDataString(envUser)}:{Uri.EscapeDataString(envPass)}@{envHost}/?authSource=admin";
    }

    //If you get a ping error run this command: docker network connect scripts_default Busable

    return null;
}

static string MaskConnectionString(string connectionString)
{
    if (string.IsNullOrEmpty(connectionString)) return connectionString;

    // Try to mask common credential patterns user:pass@host or mongodb://user:pass@...
    // This is a best-effort mask for logging only.
    try
    {
        // Replace password between ':' and '@' with '****'
        return Regex.Replace(connectionString, "(://[^:@/]+:)([^@/]+)(@)", m => $"{m.Groups[1].Value}****{m.Groups[3].Value}");
    }
    catch
    {
        return connectionString;
    }
}

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseHttpsRedirection();

app.UseAuthorization();

app.MapControllers();

app.Run();
