---
paths:
  - "src/**/*.cs"
---

# Traces e spans

A instrumentação automática do `ServiceDefaults` (ASP.NET Core, HttpClient e, quando houver, EF Core/SqlClient) já cobre requisições, chamadas HTTP de saída e banco. O consumo de evento é coberto pelo transporte escolhido no ADR (PRD 0000, Decisões delegadas a ADR), na forma da seção Consumers de evento. Código de produção não repete o que a instrumentação faz.

## Handlers HTTP

- Handler não cria span nem recebe `ActivitySource`. O span de servidor já carrega `http.route`, status e exceção.
- Handler não faz `try/catch` para registrar exceção, setar status ou devolver 500. A exceção sobe para o `UseExceptionHandler`, que responde com ProblemDetails; a instrumentação grava a exceção no span.
- Validação não abre span. Se precisar de visibilidade, uma tag no span corrente: `Activity.Current?.SetTag("app.validation.failed", true)`.

## Consumers de evento

O `<Ação>Consumer` (`program-composition.md`) segue a mesma regra do handler HTTP: o span vem de fora, e a exceção sobe.

- O span de consumo (`ActivityKind.Consumer`) é aberto pelo transporte, não pelo handler: pela instrumentação do mecanismo escolhido no ADR ou, na falta dela, por um único ponto no `ServiceDefaults` que extrai o contexto de propagação da mensagem e cria o span com os atributos `messaging.*` da semconv. O handler `<Ação>Async` roda dentro desse span e não recebe `ActivitySource`.
- Handler não faz `try/catch` para registrar exceção nem para decidir retentativa ou dead-letter. A exceção sobe para o pipeline do transporte, que grava a exceção no span e aplica a política de reprocessamento; é o equivalente do `UseExceptionHandler` para mensagens.
- O que identifica o evento vai como tag no span corrente, não como span novo: `Activity.Current?.SetTag("app.offer.id", evt.OfferId)`.
- Evento descartado por regra de negócio (ex.: `BookProcessed` recebido fora do estado esperado, OFF-33) é resultado, não falha: tag `app.event.discarded` com o motivo de baixa cardinalidade, sem exceção e sem log de erro. Assim o descarte aparece no trace sem sujar a taxa de erro do consumer.

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
- `ActivityKind.Internal` por padrão. `Client`/`Producer` só para chamada remota de saída que a instrumentação não cobre; `Consumer` é do transporte (Consumers de evento), nunca do handler.

## O que não fazer

- `SetStatus(ActivityStatusCode.Ok)`: status fica `Unset` quando não há erro.
- Eventos de start/end (`handler.start`, `query.end`, etc.): o span já tem timestamps; consultas e chamadas HTTP já viram spans filhos.
- Tags que duplicam atributos da instrumentação (`http.*`, `network.*`, `server.*`, `url.*`, `messaging.*`).
- Dado pessoal em tag ou evento: IP de cliente, documento, nome, e-mail.
- Baggage em escopo de log sem allowlist de chaves.

## Tags

- Nome semconv quando existir (`https://opentelemetry.io/docs/specs/semconv/`).
- Caso contrário, prefixo `app.` e snake_case: `app.fund.id`, `app.offer.status`.
- Valor de baixa cardinalidade. Identificador único de entidade é aceitável; payload, lista ou texto livre não.

## Logs

- Logs saem correlacionados com TraceId/SpanId automaticamente; não repetir o trace id na mensagem.
- Erro é logado uma vez, no handler global de exceção ou no pipeline do transporte, não no ponto de origem.
