---
paths:
  - "src/**/Program.cs"
  - "src/**/*Extensions.cs"
  - "src/**/*Endpoint.cs"
---

# Composição do serviço e módulos de feature

## Program.cs

`Program.cs` é composição pura. Cada linha é uma chamada de extensão; a ordem é fixa:

```csharp
using ServiceDefaults;

var builder = WebApplication.CreateSlimBuilder(args);

builder.AddServiceDefaults();
builder.AddApiDefaults();
builder.AddOfferings();            // um Add<Feature>() por módulo

var app = builder.Build();

app.UseApiDefaults();
app.MapOfferingEndpoints();        // um Map<Feature>Endpoints() por módulo

app.Run();
```

- Nenhum tipo, dado, endpoint, lambda, `if` ou `JsonSerializerContext` é declarado em `Program.cs`. O que precisa de configuração vira método de extensão: transversal em `ServiceDefaults`, específico da feature no módulo dela.
- `AddServiceDefaults()` vale para qualquer host: OpenTelemetry, health checks, service discovery, resiliência HTTP e validação do container (`ValidateOnBuild`, `ValidateScopes`) em todo ambiente.
- `AddApiDefaults()` / `UseApiDefaults()` valem só para API: versionamento por segmento de URL, `AddProblemDetails()` + `UseExceptionHandler()`, endpoints de health e `MapOpenApi()` em Development. `UseExceptionHandler()` é o middleware mais externo e depende do `AddProblemDetails()`; por isso os dois ficam juntos no `ServiceDefaults`, não no serviço.
- Uma política nova que valha para todo serviço entra nesses métodos, não em cada `Program.cs`.
- Worker segue o mesmo princípio com `Host.CreateApplicationBuilder`: `AddServiceDefaults()`, `AddHostedService<T>()`, `Build()`, `Run()`.

## Módulo de feature

Layout dentro do serviço:

```
src/<Serviço>/<Feature>/<Feature>Extensions.cs
src/<Serviço>/<Feature>/Endpoints/<Ação>/<Ação>Endpoint.cs
src/<Serviço>/<Feature>/Endpoints/<Ação>/<Ação>Request.cs      (quando houver corpo)
src/<Serviço>/<Feature>/Endpoints/<Ação>/<Ação>Response.cs     (quando o retorno não for o agregado)
```

`<Feature>Extensions` é a única porta de entrada do módulo e expõe dois métodos:

- `Add<Feature>(this IHostApplicationBuilder builder)`: registra os serviços da feature e o `JsonSerializerContext` dela em `ConfigureHttpJsonOptions(o => o.SerializerOptions.TypeInfoResolverChain.Add(<Feature>JsonContext.Default))`.
- `Map<Feature>Endpoints(this WebApplication app)`: cria o grupo com `app.NewVersionedApi("<Feature>").MapGroup("/api/v{version:apiVersion}/<recurso>").HasApiVersion(1, 0)` e chama um `Map<Ação>Endpoint(group)` por endpoint.

O `JsonSerializerContext` fica no mesmo arquivo, `internal sealed partial class <Feature>JsonContext : JsonSerializerContext`, com `[JsonSerializable]` para todo tipo de request e response da feature. Um contexto por feature; tipos compartilhados entre features vão para o contexto de quem os possui.

`<Ação>Endpoint` é uma classe estática com:

- `Map<Ação>Endpoint(this RouteGroupBuilder group)`: `MapGet`/`MapPost`/... apontando para o handler, mais metadados (`WithName`, `Produces`, `ProducesProblem`, `WithSummary`).
- Handler `private static` com nome `<Ação>Async`, dependências como parâmetros (`[FromServices]`, `[FromBody]`, `[FromQuery]`, `CancellationToken`) e retorno `TypedResults` ou `Results<...>` para que o OpenAPI saia sem reflection.
- Sem `try/catch`, sem `ActivitySource`, sem log de erro: a exceção sobe para `UseExceptionHandler`, que responde ProblemDetails (ver `tracing.md`).

## O que não fazer

- Endpoint mapeado direto em `Program.cs`, mesmo temporário.
- Registro de serviço ou de `JsonSerializerContext` fora do `Add<Feature>()` do módulo dono.
- Módulo que expõe mais do que `Add<Feature>()` e `Map<Feature>Endpoints()`: `Program.cs` não conhece o interior da feature.
