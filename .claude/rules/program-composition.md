---
paths:
  - "src/**/Program.cs"
  - "src/**/AppHost.cs"
  - "src/**/*Extensions.cs"
  - "src/**/*Endpoint.cs"
  - "src/**/*Consumer.cs"
---

# Composição do serviço e módulos de feature

Aplica-se a `Program.cs`, `AppHost.cs`, `*Extensions.cs`, `*Endpoint.cs` e `*Consumer.cs` em qualquer subdiretório de `src/`, inclusive em revisões sem edição. Os caminhos nos exemplos partem da raiz do repositório.

## Program.cs

`Program.cs` é composição pura. São permitidos `using`, criação do builder e atribuições dos objetos de composição, chamadas de registro, `Build()`, configuração do pipeline e `Run()`. Em API, os registros precedem `Build()` e `Use*`/`Map*` vêm depois:

```csharp
using ServiceDefaults;

var builder = WebApplication.CreateSlimBuilder(args);

builder.AddServiceDefaults();
builder.AddApiDefaults();
builder.AddOfferings();            // One Add<Feature>() per module

var app = builder.Build();

app.UseApiDefaults();
app.MapOfferingEndpoints();        // One Map<Feature>Endpoints() per module

app.Run();
```

- Não declare tipos, dados de negócio, handlers, lambdas de endpoint, condicionais de negócio ou `JsonSerializerContext` em `Program.cs`. Configuração transversal fica em `ServiceDefaults`; configuração e registro específicos ficam no módulo dono. As variáveis de composição do exemplo são permitidas.
- `AddServiceDefaults()` vale para qualquer host: OpenTelemetry, health checks, service discovery, resiliência HTTP e validação do container (`ValidateOnBuild`, `ValidateScopes`) em todo ambiente.
- `AddApiDefaults()` / `UseApiDefaults()` valem só para API: versionamento por segmento de URL, `AddProblemDetails()` + `UseExceptionHandler()`, endpoints de health e `MapOpenApi()` em Development. `UseExceptionHandler()` é o middleware mais externo e depende do `AddProblemDetails()`; por isso os dois ficam juntos no `ServiceDefaults`, não no serviço.
- Uma política nova que valha para todo serviço entra nesses métodos, não em cada `Program.cs`.
- Worker segue o mesmo princípio com `Host.CreateApplicationBuilder`: `AddServiceDefaults()`, `AddHostedService<T>()`, `Build()`, `Run()`.
- AppHost usa `DistributedApplication.CreateBuilder`, registros de recursos e projetos, referências e dependências entre recursos, `Build()` e `Run()`. Essas declarações expressam a topologia de execução; regras de negócio continuam nos serviços.

## Módulo de feature

Layout dentro do serviço:

```
src/<Serviço>/<Feature>/<Feature>Extensions.cs
src/<Serviço>/<Feature>/<Ação>/<Ação>Endpoint.cs
src/<Serviço>/<Feature>/<Ação>/<Ação>Request.cs      (quando houver corpo)
src/<Serviço>/<Feature>/<Ação>/<Ação>Response.cs     (quando o retorno não for o agregado)
src/<Serviço>/<Feature>/<Ação>/<Ação>Consumer.cs     (quando a ação reage a evento de outro contexto)
```

Uma feature não é só de endpoints: ela pode existir para consumir evento de outro contexto, sem expor rota. `<Feature>Extensions` é a única porta de entrada do módulo e expõe:

- `Add<Feature>(this IHostApplicationBuilder builder)`: registra os serviços da feature, seus consumers e o `JsonSerializerContext` dela em `ConfigureHttpJsonOptions(o => o.SerializerOptions.TypeInfoResolverChain.Add(<Feature>JsonContext.Default))`.
- `Map<Feature>Endpoints(this WebApplication app)`, só quando a feature expõe rota: cria o grupo com `app.NewVersionedApi("<Feature>").MapGroup("/api/v{version:apiVersion}/<recurso>").HasApiVersion(1, 0)` e chama um `Map<Ação>Endpoint(group)` por endpoint.

O `JsonSerializerContext` fica no mesmo arquivo, `internal sealed partial class <Feature>JsonContext : JsonSerializerContext`, com `[JsonSerializable]` para todo tipo de request e response da feature. Um contexto por feature; tipos compartilhados entre features vão para o contexto de quem os possui.

`<Ação>Endpoint` é uma classe estática com:

- `Map<Ação>Endpoint(this RouteGroupBuilder group)`: `MapGet`/`MapPost`/... apontando para o handler, mais metadados (`WithName`, `Produces`, `ProducesProblem`, `WithSummary`).
- Handler `private static` com nome `<Ação>Async`, dependências como parâmetros (`[FromServices]`, `[FromBody]`, `[FromQuery]`, `CancellationToken`) e retorno `TypedResults` ou `Results<...>` para que o OpenAPI saia sem reflection.
- Sem `try/catch`, sem `ActivitySource`, sem log de erro: a exceção sobe para `UseExceptionHandler`, que responde ProblemDetails (ver [tracing.md](tracing.md)).

`<Ação>Consumer` segue o mesmo molde para uma ação disparada por evento de outro contexto:

- Handler com nome `<Ação>Async`, que recebe o evento e as dependências como parâmetros, mais `CancellationToken`.
- Registrado em `Add<Feature>()`, nunca em `Program.cs`.
- Mesma regra de exceção e tracing do endpoint: sem `try/catch`, sem `ActivitySource`, sem log de erro (ver [tracing.md](tracing.md)).
- O transporte do evento não é assunto do consumer: está delegado a ADR (PRD 0000, Decisões delegadas a ADR), e o consumer não deve depender do mecanismo escolhido.

## O que não fazer

- Endpoint mapeado direto em `Program.cs`, mesmo temporário.
- Registro de serviço ou de `JsonSerializerContext` fora do `Add<Feature>()` do módulo dono.
- Módulo que expõe mais do que `Add<Feature>()` e, quando há rota, `Map<Feature>Endpoints()`: `Program.cs` não conhece o interior da feature.
