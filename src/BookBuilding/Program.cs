using ServiceDefaults;

var builder = WebApplication.CreateSlimBuilder(args);

builder.AddServiceDefaults();
builder.AddApiDefaults();

var app = builder.Build();

app.UseApiDefaults();

app.Run();
