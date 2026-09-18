# Código de produção

Projetos se aplicam a todo `src/`; composição se aplica a `Program.cs`, `AppHost.cs`, `*Extensions.cs`, `*Endpoint.cs` e `*Consumer.cs`; tracing se aplica a todo C# de produção, inclusive revisão sem edição. Caminhos dos exemplos partem da raiz.

Propriedades comuns (`TargetFramework`, `Nullable`, `ImplicitUsings`) ficam em `Directory.Build.props`. Versões de pacotes ficam em `Directory.Packages.props`: use `PackageReference` sem `Version` no projeto e `PackageVersion` no arquivo central.

Comente apenas o que o código não mostra, como o motivo de uma escolha ou uma restrição externa.

## Convenções dos projetos de produção

- Os serviços de API compilam com `PublishAot=true` e `InvariantGlobalization=true`. Evite reflection em runtime: serialização JSON usa source generation conforme o [módulo de feature](#módulo-de-feature), e bibliotecas novas precisam ser compatíveis com AOT e trimming.
- Versionamento de API via `Asp.Versioning.Http`, lido do segmento de URL, registrado por `AddApiDefaults()` do `ServiceDefaults`. O mapeamento fica no [módulo de feature](#módulo-de-feature). Todo grupo declara sua versão; não há endpoint sem versão nem versão assumida por default.
- `Asp.Versioning.OpenApi` não entra: depende de `Asp.Versioning.Mvc.ApiExplorer`, que não é compatível com AOT. O documento OpenAPI é o do `Microsoft.AspNetCore.OpenApi` puro.
- Um serviço de API novo usa `Microsoft.NET.Sdk.Web`, projeto em `src/<Nome>` e registro no AppHost. Siga a [composição do serviço](#composição-do-serviço-e-módulos-de-feature). Um worker novo segue `src/DataMigration`.

## Linguagem e fronteiras do domínio

Use no código os identificadores canônicos do glossário do PRD dono. Se faltar um conceito ou equivalente em inglês, complete o glossário do PRD dono antes de introduzir o nome no código.

Operações de negócio são nomeadas pelo motivo da mudança, como fechar ou revogar; evite `SetX` e `UpdateX`, com setters privados por padrão.

Cada contexto persiste sua visão e seus modelos. Integração ocorre por evento ou consulta ao dono, sem tabelas ou modelos compartilhados. O PRD 0000 determina a direção das dependências e lista produtor e consumidores de cada evento; o conteúdo do evento está no PRD produtor.

## Verificação de Native AOT

Build comum não comprova Native AOT. Ao mudar código de produção, publique as APIs afetadas como o job de AOT da CI em `.github/workflows/ci.yml`, com o RID da plataforma local.

## Composição do serviço e módulos de feature

### Program.cs

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

### Módulo de feature

Layout dentro do serviço:

```
src/<Serviço>/<Feature>/<Feature>Extensions.cs
src/<Serviço>/<Feature>/<Ação>/<Ação>Endpoint.cs
src/<Serviço>/<Feature>/<Ação>/<Ação>Request.cs      (quando houver corpo)
src/<Serviço>/<Feature>/<Ação>/<Ação>Response.cs     (quando o retorno não for o agregado)
src/<Serviço>/<Feature>/<Ação>/<Ação>Consumer.cs     (quando a ação reage a evento de outro contexto)
```

Uma feature não é só de endpoints: ela pode existir para consumir evento de outro contexto, sem expor rota. `<Feature>Extensions` é a única porta de entrada do módulo e expõe somente:

- `Add<Feature>(this IHostApplicationBuilder builder)`: único ponto de registro dos serviços da feature, de seus consumers e do `JsonSerializerContext` dela em `ConfigureHttpJsonOptions(o => o.SerializerOptions.TypeInfoResolverChain.Add(<Feature>JsonContext.Default))`.
- `Map<Feature>Endpoints(this WebApplication app)`, só quando a feature expõe rota: cria o grupo com `app.NewVersionedApi("<Feature>").MapGroup("/api/v{version:apiVersion}/<recurso>").HasApiVersion(1, 0)` e chama um `Map<Ação>Endpoint(group)` por endpoint.

O `JsonSerializerContext` fica no mesmo arquivo, `internal sealed partial class <Feature>JsonContext : JsonSerializerContext`, com `[JsonSerializable]` para todo tipo de request e response da feature. Um contexto por feature; tipos compartilhados entre features vão para o contexto de quem os possui.

`<Ação>Endpoint` é uma classe estática com:

- `Map<Ação>Endpoint(this RouteGroupBuilder group)`: `MapGet`/`MapPost`/... apontando para o handler, mais metadados (`WithName`, `Produces`, `ProducesProblem`, `WithSummary`).
- Handler `private static` com nome `<Ação>Async`, dependências como parâmetros (`[FromServices]`, `[FromBody]`, `[FromQuery]`, `CancellationToken`) e retorno `TypedResults` ou `Results<...>` para que o OpenAPI saia sem reflection.
- Exceções e instrumentação seguem [Handlers HTTP](#handlers-http).

`<Ação>Consumer` segue o mesmo molde para uma ação disparada por evento de outro contexto:

- Handler com nome `<Ação>Async`, que recebe o evento e as dependências como parâmetros, mais `CancellationToken`.
- Exceções e instrumentação seguem [Consumers de evento](#consumers-de-evento).
- O transporte do evento será definido em ADR; o consumer não depende do mecanismo escolhido.

## Traces e spans

A instrumentação automática do `ServiceDefaults` (ASP.NET Core, HttpClient e, quando houver, EF Core/SqlClient) já cobre requisições, chamadas HTTP de saída e banco. O consumo de evento é coberto pelo transporte, na forma da seção Consumers de evento. Código de produção não repete o que a instrumentação faz.

### Handlers HTTP

- Handler não cria span nem recebe `ActivitySource`. O span de servidor já carrega `http.route`, status e exceção.
- Handler não faz `try/catch`. A exceção sobe para o `UseExceptionHandler`, que responde com ProblemDetails; a instrumentação grava a exceção no span.
- Validação não abre span. Se precisar de visibilidade, uma tag no span corrente: `Activity.Current?.SetTag("app.validation.failed", true)`.

### Consumers de evento

Esta seção governa o `<Ação>Consumer` descrito na [composição](#composição-do-serviço-e-módulos-de-feature).

- O span de consumo (`ActivityKind.Consumer`) é aberto pelo transporte, não pelo handler: pela instrumentação do mecanismo escolhido no ADR ou, na falta dela, por um único ponto no `ServiceDefaults` que extrai o contexto de propagação da mensagem e cria o span com os atributos `messaging.*` da semconv. O handler `<Ação>Async` roda dentro desse span e não recebe `ActivitySource`.
- Handler não faz `try/catch`. A exceção sobe para o pipeline do transporte, que grava a exceção no span e decide retentativa ou dead-letter conforme a política de reprocessamento; é o equivalente do `UseExceptionHandler` para mensagens.
- O que identifica o evento vai como tag no span corrente, não como span novo: `Activity.Current?.SetTag("app.offer.id", evt.OfferId)`.
- Evento descartado por regra de negócio (ex.: `BookProcessed` recebido fora do estado esperado) é resultado, não falha: tag `app.event.discarded` com o motivo de baixa cardinalidade, sem exceção e sem log de erro. Assim o descarte aparece no trace sem sujar a taxa de erro do consumer.

### Spans manuais

- Span manual só para operação de domínio que não é requisição HTTP nem chamada de banco: cálculo de alocação, consolidação de demanda, processamento em worker.
- Sempre via `TraceAsync` do `ServiceDefaults`, que concentra `SetStatus(Error)` e `AddException`. O código de produção fica com uma linha:

```csharp
var plan = await activitySource.TraceAsync("BookBuilding.Allocate",
    ct => allocator.AllocateAsync(offer, ct), ct,
    tags: [new("app.fund.id", offer.FundId)]);
```

- `ActivitySource` vem do DI (registrado pelo `ServiceDefaults` com o nome da aplicação). Não criar instância estática nem registrar fonte nova sem `AddSource` correspondente.
- Nome do span: `Contexto.Operacao` em PascalCase, constante no serviço quando reutilizado.
- `ActivityKind.Internal` por padrão. `Client`/`Producer` só para chamada remota de saída que a instrumentação não cobre; `Consumer` é do transporte (Consumers de evento), nunca do handler.

### O que não fazer

- `SetStatus(ActivityStatusCode.Ok)`: status fica `Unset` quando não há erro.
- Eventos de start/end (`handler.start`, `query.end`, etc.): o span já tem timestamps; consultas e chamadas HTTP já viram spans filhos.
- Tags que duplicam atributos da instrumentação (`http.*`, `network.*`, `server.*`, `url.*`, `messaging.*`).
- Dado pessoal em tag ou evento: IP de cliente, documento, nome, e-mail.
- Baggage em escopo de log sem allowlist de chaves.

### Tags

- Nome semconv quando existir (`https://opentelemetry.io/docs/specs/semconv/`).
- Caso contrário, prefixo `app.` e snake_case: `app.fund.id`, `app.offer.status`.
- Valor de baixa cardinalidade. Identificador único de entidade é aceitável; payload, lista ou texto livre não.

### Logs

- Logs saem correlacionados com TraceId/SpanId automaticamente; não repetir o trace id na mensagem.
- Erro é logado uma vez, no handler global de exceção ou no pipeline do transporte, não no ponto de origem.
