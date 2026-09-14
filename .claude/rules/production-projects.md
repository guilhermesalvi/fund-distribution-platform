---
paths:
  - "src/**/*"
---

# Convenções dos projetos de produção

Complementa [CLAUDE.md](../../CLAUDE.md) para qualquer arquivo em `src/`. Os caminhos nos exemplos partem da raiz do repositório.

- Os serviços de API compilam com `PublishAot=true` e `InvariantGlobalization=true`. Evite reflection em runtime: serialização JSON usa `JsonSerializerContext` source-generated, declarado no módulo de feature que possui os tipos, e bibliotecas novas precisam ser compatíveis com AOT e trimming.
- Versionamento de API via `Asp.Versioning.Http`, lido do segmento de URL, registrado por `AddApiDefaults()` do `ServiceDefaults`. Cada módulo de feature mapeia seu grupo em `NewVersionedApi("<Nome>").MapGroup("/api/v{version:apiVersion}/<recurso>").HasApiVersion(1, 0)`. Todo grupo declara sua versão; não há endpoint sem versão nem versão assumida por default.
- `Asp.Versioning.OpenApi` não entra: depende de `Asp.Versioning.Mvc.ApiExplorer`, que não é compatível com AOT. O documento OpenAPI é o do `Microsoft.AspNetCore.OpenApi` puro.
- Um serviço de API novo segue o padrão dos existentes: `Microsoft.NET.Sdk.Web`, `CreateSlimBuilder`, `AddServiceDefaults()` + `AddApiDefaults()`, projeto em `src/<Nome>`, registrado no `.slnx` dentro da pasta `/src/` e no AppHost. Um worker novo segue `src/DataMigration`.

