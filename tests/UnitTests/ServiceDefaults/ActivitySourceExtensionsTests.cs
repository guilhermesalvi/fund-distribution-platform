using System.Diagnostics;
using ServiceDefaults;

namespace UnitTests.ServiceDefaults;

public sealed class ActivitySourceExtensionsTests : IDisposable
{
    private readonly ActivitySource _source = new($"UnitTests.{Guid.NewGuid():N}");
    private readonly ActivityListener _listener;
    private readonly List<Activity> _stopped = [];

    public ActivitySourceExtensionsTests()
    {
        _listener = new ActivityListener
        {
            ShouldListenTo = source => source.Name == _source.Name,
            Sample = (ref ActivityCreationOptions<ActivityContext> _) => ActivitySamplingResult.AllDataAndRecorded,
            ActivityStopped = _stopped.Add,
        };
        ActivitySource.AddActivityListener(_listener);
    }

    [Fact]
    public async Task Successful_operation_returns_result_and_leaves_status_unset()
    {
        var result = await _source.TraceAsync(
            "Test.Operation",
            _ => Task.FromResult(42),
            CancellationToken.None,
            tags: [new("app.test.id", "abc")]);

        Assert.Equal(42, result);
        var activity = Assert.Single(_stopped);
        Assert.Equal("Test.Operation", activity.OperationName);
        Assert.Equal(ActivityKind.Internal, activity.Kind);
        Assert.Equal(ActivityStatusCode.Unset, activity.Status);
        Assert.Equal("abc", activity.GetTagItem("app.test.id"));
        Assert.Empty(activity.Events);
    }

    [Fact]
    public async Task Failing_operation_records_error_and_exception_then_rethrows()
    {
        Func<CancellationToken, Task> operation = _ => throw new InvalidOperationException("boom");

        var exception = await Assert.ThrowsAsync<InvalidOperationException>(
            () => _source.TraceAsync("Test.Operation", operation, CancellationToken.None));

        Assert.Equal("boom", exception.Message);
        var activity = Assert.Single(_stopped);
        Assert.Equal(ActivityStatusCode.Error, activity.Status);
        Assert.Equal("boom", activity.StatusDescription);
        var activityEvent = Assert.Single(activity.Events);
        Assert.Equal("exception", activityEvent.Name);
    }

    public void Dispose()
    {
        _listener.Dispose();
        _source.Dispose();
    }
}
