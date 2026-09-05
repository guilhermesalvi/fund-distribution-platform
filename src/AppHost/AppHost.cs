var builder = DistributedApplication.CreateBuilder(args);

builder.AddProject<Projects.DataMigration>("data-migration");

builder.AddProject<Projects.Offering>("offering")
    .WithHttpHealthCheck("/health");

builder.AddProject<Projects.ReservationBook>("reservation-book")
    .WithHttpHealthCheck("/health");

builder.AddProject<Projects.Allocation>("allocation")
    .WithHttpHealthCheck("/health");

builder.Build().Run();
