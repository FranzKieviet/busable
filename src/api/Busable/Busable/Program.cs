using Busable.Business.Interfaces;
using Busable.Business.Services;
using Busable.Data.Interfaces;
using Busable.Data.Repositories;
using MongoDB.Bson;
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
var mongoConnectionString = builder.Configuration.GetValue<string>("Mongo:ConnectionString")
    ?? Environment.GetEnvironmentVariable("MONGO_CONNECTION")
    ?? BuildMongoConnectionStringFromEnv()
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
var collectionName = Environment.GetEnvironmentVariable("MONGO_COLLECTION_NAME")
    ?? "stops_ac-transit_20260713_130403";

builder.Services.AddSingleton<IBusStopsRepository>(sp =>
    new BusStopRepository(sp.GetRequiredService<IMongoDatabase>(), collectionName));
builder.Services.AddScoped<IBusStopsService, BusStopsService>();

// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();

var app = builder.Build();

// Verify MongoDB connectivity at startup to fail fast and log a helpful message.
var logger = app.Services.GetRequiredService<ILogger<Program>>();
try
{
    // Allow overriding connection details via environment variables for containers.
    // Priority:
    // 1. MONGO_CONNECTION - full connection string (e.g. mongodb://user:pass@host:27017/?authSource=admin)
    // 2. MONGO_USER, MONGO_PASSWORD, MONGO_HOST (build connection string and use authSource=admin)
    // 3. fallback to the IMongoClient registered in DI (existing behavior)

    var envConn = Environment.GetEnvironmentVariable("MONGO_CONNECTION");
    if (!string.IsNullOrWhiteSpace(envConn))
    {
        client = new MongoClient(envConn);
        logger.LogInformation("Using MongoDB connection from MONGO_CONNECTION env var.");
    }
    else
    {
        var envUser = Environment.GetEnvironmentVariable("MONGO_USER");
        var envPass = Environment.GetEnvironmentVariable("MONGO_PASSWORD");
        var envHost = Environment.GetEnvironmentVariable("MONGO_HOST");

        if (!string.IsNullOrWhiteSpace(envUser) && !string.IsNullOrWhiteSpace(envPass) && !string.IsNullOrWhiteSpace(envHost))
        {
            var built = $"mongodb://{Uri.EscapeDataString(envUser)}:{Uri.EscapeDataString(envPass)}@{envHost}/?authSource=admin";
            client = new MongoClient(built);
            logger.LogInformation("Using MongoDB connection from MONGO_USER/MONGO_PASSWORD/MONGO_HOST env vars.");
        }
        else
        {
            // Fall back to the registered client from DI
            client = app.Services.GetRequiredService<IMongoClient>() as MongoClient ?? new MongoClient(mongoConnectionString);
            logger.LogInformation("Using MongoDB client from DI or configured connection string.");
        }
    }

    var db = client.GetDatabase(mongoDatabaseName);

    // Ping the server; this will throw if the server is unreachable or auth fails.
    db.RunCommand<BsonDocument>(new BsonDocument("ping", 1));

    logger.LogInformation("Successfully connected to MongoDB database '{DatabaseName}'. Connection: {ConnectionStringMasked}",
        mongoDatabaseName, MaskConnectionString(envConn ?? mongoConnectionString));
}
catch (Exception ex)
{
    logger.LogError(ex, "Failed to connect to MongoDB. Connection string (masked): {ConnectionStringMasked}",
        MaskConnectionString(Environment.GetEnvironmentVariable("MONGO_CONNECTION") ?? mongoConnectionString));
    // Re-throw to prevent the app from running in a bad state.
    throw;
}

static string? BuildMongoConnectionStringFromEnv()
{
    var envUser = Environment.GetEnvironmentVariable("MONGO_USER");
    var envPass = Environment.GetEnvironmentVariable("MONGO_PASSWORD");
    var envHost = Environment.GetEnvironmentVariable("MONGO_HOST");
    if (!string.IsNullOrWhiteSpace(envUser) && !string.IsNullOrWhiteSpace(envPass) && !string.IsNullOrWhiteSpace(envHost))
    {
        return $"mongodb://{Uri.EscapeDataString(envUser)}:{Uri.EscapeDataString(envPass)}@{envHost}/?authSource=admin";
    }

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
