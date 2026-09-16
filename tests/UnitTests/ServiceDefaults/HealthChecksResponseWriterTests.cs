using System.Text.Json;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.Diagnostics.HealthChecks;
using ServiceDefaults;

namespace UnitTests.ServiceDefaults;

public class HealthChecksResponseWriterTests
{
    [Fact]
    public async Task Writes_report_as_camel_case_json_and_omits_null_descriptions()
    {
        var context = new DefaultHttpContext();
        context.Response.Body = new MemoryStream();
        var report = new HealthReport(
            new Dictionary<string, HealthReportEntry>
            {
                ["self"] = new(HealthStatus.Healthy, description: null, TimeSpan.FromMilliseconds(2), exception: null, data: null),
                ["database"] = new(HealthStatus.Degraded, "slow", TimeSpan.FromMilliseconds(30), exception: null, data: null),
            },
            TimeSpan.FromMilliseconds(32));

        await HealthChecksResponseWriter.WriteJsonAsync(context, report);

        Assert.StartsWith("application/json", context.Response.ContentType);
        Assert.Equal("no-store", context.Response.Headers.CacheControl.ToString());

        context.Response.Body.Position = 0;
        using var json = await JsonDocument.ParseAsync(context.Response.Body);
        var root = json.RootElement;
        Assert.Equal("Degraded", root.GetProperty("status").GetString());
        Assert.Equal(32, root.GetProperty("totalDurationMs").GetDouble());

        var entries = root.GetProperty("entries");
        var self = entries.GetProperty("self");
        Assert.Equal("Healthy", self.GetProperty("status").GetString());
        Assert.Equal(2, self.GetProperty("durationMs").GetDouble());
        Assert.False(self.TryGetProperty("description", out _));
        Assert.Equal("slow", entries.GetProperty("database").GetProperty("description").GetString());
    }
}
