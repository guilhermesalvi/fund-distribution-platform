---
paths:
  - "src/**/*.cs"
---

# Traces e spans

A instrumentação automática do `ServiceDefaults` (ASP.NET Core, HttpClient e, quando houver, EF Core/SqlClient) já cobre requisições, chamadas HTTP de saída e banco. Código de produção não repete o que ela faz.

## Handlers HTTP

- Handler não cria span nem recebe `ActivitySource`. O span de servidor já carrega `http.route`, status e exceção.
- Handler não faz `try/catch` para registrar exceção, setar status ou devolver 500. A exceção sobe para o `UseExceptionHandler`, que responde com ProblemDetails; a instrumentação grava a exceção no span.
- Validação não abre span. Se precisar de visibilidade, uma tag no span corrente: `Activity.Current?.SetTag("app.validation.failed", true)`.

## Spans manuais

- Span manual só para operação de domínio que não é requisição HTTP nem chamada de banco: cálculo de alocação, consolidação de demanda, processamento em worker.
- Sempre via `TraceAsync` do `ServiceDefaults`, que concentra `SetStatus(Error)` e `AddException`. O código de produção fica com uma linha:

```csharp
var plan = await activitySource.TraceAsync("Allocation.Distribute",
    ct => allocator.DistributeAsync(offer, ct), ct,
    tags: [new("app.fund.id", offer.FundId)]);
```

- `ActivitySource` vem do DI (registrado pelo `ServiceDefaults` com o nome da aplicação). Não criar instância estática nem registrar fonte nova sem `AddSource` correspondente.
- Nome do span: `Contexto.Operacao` em PascalCase, constante no serviço quando reutilizado.
- `ActivityKind.Internal` por padrão. `Client`/`Producer` só para chamada remota de saída que a instrumentação não cobre.

## O que não fazer

- `SetStatus(ActivityStatusCode.Ok)`: status fica `Unset` quando não há erro.
- Eventos de start/end (`handler.start`, `query.end`, etc.): o span já tem timestamps; consultas e chamadas HTTP já viram spans filhos.
- Tags que duplicam atributos da instrumentação (`http.*`, `network.*`, `server.*`, `url.*`).
- Dado pessoal em tag ou evento: IP de cliente, documento, nome, e-mail.
- Baggage em escopo de log sem allowlist de chaves.

## Tags

- Nome semconv quando existir (`https://opentelemetry.io/docs/specs/semconv/`).
- Caso contrário, prefixo `app.` e snake_case: `app.fund.id`, `app.offer.status`.
- Valor de baixa cardinalidade. Identificador único de entidade é aceitável; payload, lista ou texto livre não.

## Logs

- Logs saem correlacionados com TraceId/SpanId automaticamente; não repetir o trace id na mensagem.
- Erro é logado uma vez, no handler global de exceção, não no ponto de origem.
