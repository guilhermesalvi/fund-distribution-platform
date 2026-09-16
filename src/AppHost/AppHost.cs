var builder = DistributedApplication.CreateBuilder(args);

builder.AddProject<Projects.DataMigration>("data-migration");

builder.AddProject<Projects.Offering>("offering")
    .WithHttpHealthCheck("/health");

builder.AddProject<Projects.BookBuilding>("book-building")
    .WithHttpHealthCheck("/health");

builder.Build().Run();
