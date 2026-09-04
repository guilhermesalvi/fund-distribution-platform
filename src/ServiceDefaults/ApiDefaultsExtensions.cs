using Asp.Versioning;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

namespace ServiceDefaults;

// Defaults shared by every API service, on top of AddServiceDefaults: URL segment API versioning,
// ProblemDetails error responses and the OpenAPI document. Workers do not use these.
public static class ApiDefaultsExtensions
{
    public static WebApplicationBuilder AddApiDefaults(this WebApplicationBuilder builder)
    {
        // Versioning is read from the URL segment (e.g. /api/v1/...). Every endpoint group must
        // declare its own version, so no default is assumed for unversioned routes.
        builder.Services.AddApiVersioning(options =>
        {
            options.DefaultApiVersion = new ApiVersion(1, 0);
            options.ApiVersionReader = new UrlSegmentApiVersionReader();
            options.ReportApiVersions = true;
        });

        builder.Services.AddProblemDetails();
        builder.Services.AddOpenApi();

        return builder;
    }

    public static WebApplication UseApiDefaults(this WebApplication app)
    {
        // Outermost middleware: unhandled exceptions become a generic ProblemDetails response.
        app.UseExceptionHandler();

        app.MapDefaultEndpoints();

        if (app.Environment.IsDevelopment())
        {
            app.MapOpenApi();
        }

        return app;
    }
}
