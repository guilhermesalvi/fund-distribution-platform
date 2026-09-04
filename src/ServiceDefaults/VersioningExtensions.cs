using Asp.Versioning;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

namespace ServiceDefaults;

// API versioning read from the URL segment (e.g. /api/v1/...). Every endpoint group must declare
// its own version, so no default is assumed for unversioned routes.
public static class VersioningExtensions
{
    public static TBuilder AddDefaultApiVersioning<TBuilder>(this TBuilder builder) where TBuilder : IHostApplicationBuilder
    {
        builder.Services.AddApiVersioning(options =>
        {
            options.DefaultApiVersion = new ApiVersion(1, 0);
            options.ApiVersionReader = new UrlSegmentApiVersionReader();
            options.ReportApiVersions = true;
        });

        return builder;
    }
}
