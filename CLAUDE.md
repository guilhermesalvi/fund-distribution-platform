# CLAUDE.md

Instruções para agentes trabalhando neste repositório.

## Idioma

- Código, identificadores, nomes de arquivos e diretórios, comentários, logs, mensagens de erro e mensagens de commit: **inglês**.
- Texto de documentação (`.md`, ADRs, notas): **português**.

## Convenção de commits

Conventional Commits, com o template:

```
<type>: <description_in_english>
```

Regras:

- Máximo de **60 caracteres** na linha inteira, incluindo `<type>: `. O GitHub trunca o título do commit a partir de 72 caracteres; 60 mantém folga sem afrouxar a disciplina.
- Sem escopo — nada de `feat(api):`.
- Sem ponto final.
- Sem corpo (header) e sem rodapé (footer). A mensagem é uma única linha.
- Sem `!` para breaking changes — breaking changes são comunicados na descrição do pull request.
- `<type>` em minúsculas; `<description>` em inglês, imperativo, minúscula inicial.

Tipos: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `build`, `ci`, `chore`, `style`, `revert`.

Exemplos:

```
feat: add user endpoint
fix: handle null distribution amount
refactor: extract fund allocation service
test: cover partial distribution scenario
chore: bump target framework to net10
```

## Granularidade dos commits

O critério de agrupamento é o **motivo da mudança**, não o tipo de arquivo.

- Arquivos alterados pelo mesmo motivo vão no mesmo commit, mesmo que cruzem camadas. Um refactor que toca código de produção, testes e documentação é um único `refactor: anything`.
- Arquivos alterados por motivos diferentes vão em commits diferentes, mesmo que estejam no mesmo diretório ou tenham sido tocados na mesma sessão de trabalho.
- Cada commit deve deixar o repositório em estado consistente: compilando e com os testes passando.
- Na dúvida sobre o `<type>` de um commit que mistura camadas, use o tipo do motivo da mudança — o refactor que também ajustou testes é `refactor`, não `test`.

## Estrutura da solução

Solução `FundDistributionPlatform.slnx`, .NET 10, orquestrada com .NET Aspire.

- `src/AppHost` — Aspire AppHost (SDK `Aspire.AppHost.Sdk`). Ponto de entrada para rodar a plataforma localmente.
- `src/ServiceDefaults` — projeto compartilhado do Aspire: OpenTelemetry, service discovery, resiliência HTTP e health checks. Todo serviço deve referenciá-lo e chamar `AddServiceDefaults()`.
- `src/Offering`, `src/DemandConsolidation`, `src/ReservationBook`, `src/Allocation` — serviços ASP.NET Core minimal API, um por contexto de domínio.
- `tests/UnitTests`, `tests/IntegrationTests` — xUnit.

## Build e testes

```
dotnet build FundDistributionPlatform.slnx
dotnet test FundDistributionPlatform.slnx
```

Valide os dois antes de encerrar qualquer mudança em código.

## Convenções de projeto

- Versões de pacote são centralizadas em `Directory.Packages.props` (Central Package Management). `PackageReference` nos csproj **não leva `Version`**; pacote novo entra como `PackageVersion` no props e como `PackageReference` sem versão no csproj.
- Os serviços compilam com `PublishAot=true` e `InvariantGlobalization=true`. Evite reflection em runtime: serialização JSON usa `JsonSerializerContext` source-generated (ver `AppJsonSerializerContext` em cada `Program.cs`), e bibliotecas novas precisam ser compatíveis com AOT e trimming.
- Um serviço novo segue o padrão dos existentes: `Microsoft.NET.Sdk.Web`, `CreateSlimBuilder`, projeto em `src/<Nome>`, registrado no `.slnx` dentro da pasta `/src/` e no AppHost.
