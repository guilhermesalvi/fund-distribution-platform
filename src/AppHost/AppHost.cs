var builder = DistributedApplication.CreateBuilder(args);

builder.AddProject<Projects.DataMigration>("data-migration");

builder.AddProject<Projects.Offering>("offering")
    .WithHttpHealthCheck();

builder.AddProject<Projects.DemandConsolidation>("demand-consolidation")
    .WithHttpHealthCheck();

builder.AddProject<Projects.ReservationBook>("reservation-book")
    .WithHttpHealthCheck();

builder.AddProject<Projects.Allocation>("allocation")
    .WithHttpHealthCheck();

builder.Build().Run();
