using ServiceDefaults;

var builder = WebApplication.CreateSlimBuilder(args);

builder.AddServiceDefaults();
builder.AddDefaultApiVersioning();
builder.Services.AddOpenApi();

var app = builder.Build();

app.MapDefaultEndpoints();

if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.Run();
