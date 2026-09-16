using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Diagnostics.HealthChecks;

namespace ServiceDefaults;

public static class HealthChecksResponseWriter
{
    public static async Task WriteJsonAsync(HttpContext httpContext, HealthReport report)
    {
        httpContext.Response.ContentType = "application/json; charset=utf-8";
        httpContext.Response.Headers.CacheControl = "no-store";

        var response = new HealthCheckResponse(
            Status: report.Status.ToString(),
            TotalDurationMs: report.TotalDuration.TotalMilliseconds,
            Entries: report.Entries.ToDictionary(
                kvp => kvp.Key,
                kvp => new HealthCheckEntry(
                    Status: kvp.Value.Status.ToString(),
                    DurationMs: kvp.Value.Duration.TotalMilliseconds,
                    Description: kvp.Value.Description)));

        await httpContext.Response.WriteAsJsonAsync(
            response,
            HealthChecksJsonSerializerContext.Default.HealthCheckResponse,
            cancellationToken: httpContext.RequestAborted);
    }
}

public sealed record HealthCheckEntry(string Status, double DurationMs, string? Description);

public sealed record HealthCheckResponse(
    string Status,
    double TotalDurationMs,
    Dictionary<string, HealthCheckEntry> Entries);

[JsonSourceGenerationOptions(
    PropertyNamingPolicy = JsonKnownNamingPolicy.CamelCase,
    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull)]
[JsonSerializable(typeof(HealthCheckResponse))]
internal sealed partial class HealthChecksJsonSerializerContext : JsonSerializerContext;
