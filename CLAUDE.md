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
- `src/ServiceDefaults` — projeto compartilhado do Aspire: OpenTelemetry, service discovery, resiliência HTTP, health checks e validação do container. Todo serviço deve referenciá-lo e chamar `AddServiceDefaults()`. Serviços de API chamam também `AddApiDefaults()` / `UseApiDefaults()`: versionamento, ProblemDetails e OpenAPI.
- `src/Offering`, `src/ReservationBook`, `src/Allocation` — serviços ASP.NET Core minimal API, um por contexto de domínio.
- `src/DataMigration` — Worker Service (`Microsoft.NET.Sdk.Worker`) para migração de dados. Não expõe HTTP e não compila com AOT.
- `tests/UnitTests`, `tests/IntegrationTests` — xUnit.

## Build e testes

```
dotnet build FundDistributionPlatform.slnx
dotnet test FundDistributionPlatform.slnx
```

Valide os dois antes de encerrar qualquer mudança em código.

## Convenções de projeto

- Propriedades comuns a todos os projetos (`TargetFramework`, `Nullable`, `ImplicitUsings`) ficam em `Directory.Build.props`; os csproj não as repetem.
- Versões de pacote são centralizadas em `Directory.Packages.props` (Central Package Management). `PackageReference` nos csproj **não leva `Version`**; pacote novo entra como `PackageVersion` no props e como `PackageReference` sem versão no csproj.
- Os serviços de API compilam com `PublishAot=true` e `InvariantGlobalization=true`. Evite reflection em runtime: serialização JSON usa `JsonSerializerContext` source-generated, declarado no módulo de feature que possui os tipos, e bibliotecas novas precisam ser compatíveis com AOT e trimming.
- Versionamento de API via `Asp.Versioning.Http`, lido do segmento de URL, registrado por `AddApiDefaults()` do `ServiceDefaults`. Cada módulo de feature mapeia seu grupo em `NewVersionedApi("<Nome>").MapGroup("/api/v{version:apiVersion}/<recurso>").HasApiVersion(1, 0)`. Todo grupo declara sua versão; não há endpoint sem versão nem versão assumida por default.
- `Program.cs` é composição pura: cada linha é uma chamada de extensão (`Add*` antes do `Build()`, `Use*`/`Map*` depois). Nenhum tipo, dado, endpoint, lambda, `if` ou `JsonSerializerContext` é declarado nele; o que é comum a todo serviço vive no `ServiceDefaults`.
- `Asp.Versioning.OpenApi` não entra: depende de `Asp.Versioning.Mvc.ApiExplorer`, que não é compatível com AOT. O documento OpenAPI é o do `Microsoft.AspNetCore.OpenApi` puro.
- Um serviço de API novo segue o padrão dos existentes: `Microsoft.NET.Sdk.Web`, `CreateSlimBuilder`, `AddServiceDefaults()` + `AddApiDefaults()`, projeto em `src/<Nome>`, registrado no `.slnx` dentro da pasta `/src/` e no AppHost. Um worker novo segue `src/DataMigration`.

## Linguagem do domínio

Princípios extraídos da mentoria de arquitetura de software do Elemar Jr. (2026), na parte que se aplica a este repositório. Cada regra vem com o princípio que a justifica; quem conhece o princípio pode julgar quando a regra não cabe.

- **Conceito antes de termo.** O que se modela é o conceito: seu significado e suas relações com os outros conceitos. O termo é rótulo. Uma decisão de nome começa por fixar o significado; só depois se escolhe a palavra. *Princípio:* semântica pesa mais que sintaxe; a maior parte das discussões de nomenclatura erra por discutir a palavra sem fixar o significado.
- **Um conceito, uma comunidade semântica por idioma.** Os PRDs falam a língua do mercado brasileiro de ofertas públicas (CVM, coordenadores, administradores); o código fala a língua da comunidade anglófona equivalente (prospectos, Takeover Code, Companies Act). O identificador em inglês não é tradução literal do termo em português: é o termo que aquela comunidade usa para o mesmo conceito, verificado em fonte primária (prospecto, norma, código de conduta), com a fonte citada na decisão. Exemplo: a oferta que não atinge o montante mínimo é `Lapsed`, termo dos prospectos, e não `NotFormed`. *Princípio:* DDD não se importa com o idioma, se importa com o conceito compartilhado; um termo que só faz sentido para quem leu o PRD em português não é linguagem ubíqua.
- **Sem termo consagrado, espelhe o português e registre.** Quando a comunidade anglófona não tem um termo para o conceito, diga isso explicitamente, use o espelho do termo em português e registre a decisão com a lacuna. Não invente um termo que pareça idiomático mas carregue outro significado naquela comunidade.
- **Colisão de significado é defeito.** Um termo que, na mesma comunidade, já tem outro sentido (ex.: "Cancelada" para mínimo não atingido, quando a CVM 160 usa cancelamento para ato da CVM por irregularidade) é defeito de nomenclatura, mesmo que o glossário o esclareça. Aponte e proponha o termo que não colide.
- **Sinônimos e fronteiras.** Quando especialistas usam termos diferentes para o mesmo conceito, escolha um canônico e registre os demais como sinônimos no glossário. Quando usam o mesmo termo para conceitos diferentes, é indício de fronteira entre contextos: não unifique, e cheque se o contexto está bem delimitado. *Princípio:* um bounded context é o esforço de criar uma comunidade semântica; a fronteira aparece onde a linguagem muda.
- **O glossário do PRD é a fonte dos nomes.** Cada PRD carrega o glossário do seu contexto: conceito, significado e, quando importa, as relações entre conceitos. As relações valem mais que a lista de conceitos. Nome de tipo, estado, evento ou campo no código nasce do glossário; se o código precisa de um conceito que o glossário não tem, o glossário muda primeiro.
- **Do texto ao modelo em etapas.** Ao extrair modelo de uma conversa, transcrição ou norma: conceitos e significados → relações entre conceitos → instâncias e classes → atributos → restrições. Não salte da transcrição para o modelo de classes; cada etapa é validável com o especialista antes da seguinte.
- **Operações com nome de negócio.** O modelo é tão anêmico quanto deixa de expressar os motivos de mudança de estado. Nada de `SetX`/`UpdateX`: a operação recebe o nome do que aconteceu no domínio (fechar o livro, revogar a oferta, processar o livro). Setters são privados por padrão. Evento de domínio é o reconhecimento de uma operação que mudou o estado e existe para informar outro contexto; não emita evento que ninguém consome.
- **Contextos não compartilham persistência.** Cada contexto persiste a sua visão do conceito; integração entre contextos é por evento ou consulta ao dono, nunca por tabela ou modelo compartilhado. O contexto core (Offering) é upstream: mudança incompatível de contrato só é tolerada partindo dele.

## Decisões e complexidade

- **Toda decisão tem um lado ruim.** Uma decisão de arquitetura ou de modelo só está pronta quando seu custo está nomeado. Os PRDs registram decisões com *Custo* e *Razão*; mantenha esse formato. Se não há lado ruim identificado, a decisão não foi analisada.
- **Regra tem princípio.** Toda instrução deste arquivo carrega o porquê. Antes de aplicar um padrão (camada, interface, abstração, mediator, repositório) pergunte qual necessidade concreta ele atende neste repositório. Sem necessidade, não entra: complexidade desnecessária é custo, e reduzir acoplamento além do necessário destrói coesão.
- **Consciência situacional antes de julgar.** Antes de propor mudança em algo existente, leia o PRD, a decisão registrada e o histórico do git. Uma decisão que parece errada em geral tem um contexto que não está à vista. Substitua afirmações por perguntas até o contexto aparecer.
- **Critérios, não instruções de como.** Ao pedir ou propor um design, explicite os critérios pelos quais a solução será avaliada; ao receber critérios, critique-os e aponte o que falta antes de propor. Em decisão de design, apresente mais de uma opção com os trade-offs e tome partido; uma única solução apresentada como "a resposta" é sinal de análise incompleta.
- **Determinístico onde puder.** Verificação é build, teste e analisador estático, não leitura de código por IA. Onde há lógica de domínio há teste; getter e setter não se testa. Processo repetível vira script no repositório, não prompt repetido.
- **Código para humanos.** O código gerado com IA segue as convenções deste arquivo e deve ser mantido sem IA, se preciso. Revise este arquivo quando instruções conflitarem entre si; instrução conflitante degrada o resultado mais que instrução faltando.
