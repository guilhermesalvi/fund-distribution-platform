using System.Diagnostics;

namespace ServiceDefaults;

// Wraps a domain operation in an activity, recording exceptions and error status in one place
// so that production code stays free of tracing boilerplate. Status is left Unset on success,
// as recommended by the OpenTelemetry specification.
public static class ActivitySourceExtensions
{
    public static async Task<TResult> TraceAsync<TResult>(
        this ActivitySource source,
        string name,
        Func<CancellationToken, Task<TResult>> operation,
        CancellationToken cancellationToken,
        ActivityKind kind = ActivityKind.Internal,
        IEnumerable<KeyValuePair<string, object?>>? tags = null)
    {
        using var activity = source.StartActivity(name, kind, default(ActivityContext), tags);

        try
        {
            return await operation(cancellationToken);
        }
        catch (Exception ex)
        {
            RecordFailure(activity, ex);
            throw;
        }
    }

    public static async Task TraceAsync(
        this ActivitySource source,
        string name,
        Func<CancellationToken, Task> operation,
        CancellationToken cancellationToken,
        ActivityKind kind = ActivityKind.Internal,
        IEnumerable<KeyValuePair<string, object?>>? tags = null)
    {
        using var activity = source.StartActivity(name, kind, default(ActivityContext), tags);

        try
        {
            await operation(cancellationToken);
        }
        catch (Exception ex)
        {
            RecordFailure(activity, ex);
            throw;
        }
    }

    private static void RecordFailure(Activity? activity, Exception exception)
    {
        if (activity is null)
        {
            return;
        }

        activity.SetStatus(ActivityStatusCode.Error, exception.Message);
        activity.AddException(exception);
    }
}
