using System.Net;
using Aspire.Hosting;
using Aspire.Hosting.ApplicationModel;
using Aspire.Hosting.Testing;

namespace IntegrationTests;

public class AppHostTests
{
    private static readonly TimeSpan StartupTimeout = TimeSpan.FromSeconds(120);

    [Theory]
    [InlineData("offering")]
    [InlineData("book-building")]
    public async Task Api_starts_and_reports_healthy(string resourceName)
    {
        var appHost = await DistributedApplicationTestingBuilder.CreateAsync<Projects.AppHost>();
        await using var app = await appHost.BuildAsync();
        await app.StartAsync();

        await app.ResourceNotifications.WaitForResourceHealthyAsync(resourceName).WaitAsync(StartupTimeout);

        using var client = app.CreateHttpClient(resourceName);
        using var response = await client.GetAsync("/health");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task Worker_starts_and_keeps_running()
    {
        var appHost = await DistributedApplicationTestingBuilder.CreateAsync<Projects.AppHost>();
        await using var app = await appHost.BuildAsync();
        await app.StartAsync();

        await app.ResourceNotifications
            .WaitForResourceAsync("data-migration", KnownResourceStates.Running)
            .WaitAsync(StartupTimeout);
    }
}
