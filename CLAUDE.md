# CLAUDE.md

Instruções para o Claude Code trabalhando neste repositório.

## Uso com Claude Code

Este arquivo é a entrada das convenções do projeto. Todos os caminhos abaixo são relativos à raiz do repositório; execute os comandos de build e validação a partir dela, inclusive quando a tarefa começar em um subdiretório.

As regras do código de produção ficam em `.claude/rules/` e carregam sozinhas quando um arquivo do padrão declarado no frontmatter `paths` de cada uma entra na tarefa; as regras se acumulam quando os padrões coincidem. Ao revisar código em `src/` sem editá-lo, leia antes as regras da área:

- [Convenções dos projetos de produção](.claude/rules/production-projects.md): qualquer arquivo em `src/`. Native AOT, versionamento de API e padrão de serviço novo.
- [Composição do serviço e módulos de feature](.claude/rules/program-composition.md): `Program.cs`, `AppHost.cs`, `*Extensions.cs`, `*Endpoint.cs` e `*Consumer.cs` em `src/`.
- [Traces e spans](.claude/rules/tracing.md): todo `.cs` em `src/`.

As skills `prd` (requisitos de produto) e `sdd` (especificação, design, execução e verificação técnica) vêm do plugin `claude-skills`, instalado na conta e não no repositório, e aparecem no menu `/` como `/claude-skills:prd` e `/claude-skills:sdd`. O Claude Code também as carrega sozinho quando a descrição corresponde à tarefa. As skills dão precedência às convenções deste arquivo sobre seus defaults; o que o repositório fixa está em Idioma e em Estrutura da solução. Pedidos gerais de documentação e mudanças mecânicas não exigem abrir um fluxo de produto ou SDD.

Preserve o escopo, as decisões delegadas e as autorizações da sessão. Um pedido de análise ou planejamento termina na entrega solicitada. Em implementação autorizada, decida as opções técnicas, registre custos relevantes e conclua as correções e verificações necessárias; apresentações intermediárias informam progresso. Aprovação de conteúdo e autorização de Git são distintas: commit registra uma versão e não é pré-requisito para usar ou verificar arquivos atuais. Commit, push, deploy e decisões de negócio seguem a autorização da mudança.

Pergunte apenas quando faltar informação indispensável que o contexto não resolve. Se perguntas forem vedadas, registre a lacuna e conclua o trabalho independente, sem inventar uma decisão de negócio. Continue enquanto houver correção fundamentada ou nova evidência; repetir uma tentativa sem mudança nem hipótese não é progresso. Quando houver bloqueio real, informe a ação impedida, sua causa e a decisão ou recurso necessário. Se uma instrução local causar a pausa, confira sua precedência e cite o arquivo e a regra exata.

Instalação do plugin, decisões de layout e verificação de descoberta: [docs/development/claude-code.md](docs/development/claude-code.md). Ao mudar instruções, regras ou a estrutura da solução, confira o `.slnx` (Arquivos no `.slnx`) e confirme a descoberta em uma nova sessão na raiz e em `src/Offering`, conforme o guia.

## Idioma

- Código, identificadores, nomes de arquivos e diretórios, comentários, logs, mensagens de erro e mensagens de commit: **inglês**.
- Textos instrucionais das regras em `.claude/rules`: **português do Brasil**.
- Documentação (`.md`, ADRs, notas): **português** na prosa e nos títulos livres. Títulos, rótulos, tags e campos que são contratos de artefatos permanecem em **inglês**, como as skills `prd` e `sdd` definem (estrutura em inglês, prosa na língua do artefato). A prosa em português é convenção deste repositório e prevalece sobre o default de idioma das skills. Preserve IDs, palavras-chave EARS, código e identificadores técnicos.

## Convenção de commits

Conventional Commits, com o template:

```
<type>: <description_in_english>
```

Regras:

- Máximo de **60 caracteres** na linha inteira, incluindo `<type>: `. O GitHub trunca o título do commit a partir de 72 caracteres; 60 mantém folga sem afrouxar a disciplina.
- Sem escopo — nada de `feat(api):`.
- Sem ponto final.
- Sem corpo (body) e sem rodapé (footer). A mensagem é uma única linha.
- Sem `!` para breaking changes — breaking changes são comunicados na descrição do pull request.
- `<type>` em minúsculas; `<description>` em inglês, imperativo, minúscula inicial.

Tipos: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `build`, `ci`, `chore`, `style`, `revert`.

Confira a mensagem contra estas regras antes de commitar; não há validação automática.

O commit é de autoria de quem pediu a mudança, com o `user.name` e o `user.email` do próprio usuário; nada de trailer de ferramenta (`Co-Authored-By`, `Generated-by`), porque a regra de rodapé acima vale para qualquer origem da mensagem. Quando o ambiente não tem autor configurado, passe `-c user.name=… -c user.email=…` no commit em vez de configurar a máquina.

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
- `src/Offering`, `src/BookBuilding` — serviços ASP.NET Core minimal API, um por contexto de domínio.
- `src/DataMigration` — Worker Service (`Microsoft.NET.Sdk.Worker`) para migração de dados. Não expõe HTTP e não compila com AOT.
- `tests/UnitTests` — xUnit; referencia `ServiceDefaults` e testa lógica sem host (`TraceAsync`, writer de health checks). Os testes de domínio de cada contexto entram aqui, em pasta por contexto, junto com a implementação.
- `tests/IntegrationTests` — xUnit com `Aspire.Hosting.Testing`; sobe o AppHost e verifica que cada recurso inicia e responde `/health`. Exige a Aspire CLI instalada, porque o AppHost usa o bundle da CLI (`AspireUseCliBundle`).
- `docs/prd` — PRDs, um por capability mais o `0000` de visão geral: `0001` do Offering, `0002` e `0003` do BookBuilding. O prefixo de requisito é por PRD e único na pasta, então um contexto pode ter mais de um (`BOOK` e `ALLOC`); essa convenção do repositório prevalece sobre o default "um prefixo por contexto" da skill. Escritos e revisados com `/claude-skills:prd`. Spec, design e tasks de cada capability nascem de `/claude-skills:sdd` em `docs/specs`.
- `.claude/rules` — regras por área do código de produção, carregadas pelo padrão de arquivo (Uso com Claude Code).

### Arquivos no `.slnx`

Todo arquivo versionado aparece no Solution Explorer: arquivos internos a um projeto são exibidos pelo próprio projeto; os demais entram explicitamente no `.slnx`, espelhando o layout das pastas em disco. *Princípio:* o `.slnx` é a visão do repositório no Solution Explorer; artefato fora dele é invisível para quem navega pela IDE.

- Cada diretório vira `<Folder Name="/caminho/completo/">`, com o caminho desde a raiz e barras no início e no fim. Diretório intermediário sem arquivo próprio é declarado vazio (`<Folder Name="/docs/" />`) antes dos filhos.
- Arquivo não-projeto entra como `<File Path="caminho/relativo/arquivo.md" />` dentro da pasta que corresponde ao seu diretório.
- Projeto (`.csproj`) entra como `<Project Path="..." />` na pasta do diretório que o contém (`/src/`, `/tests/`), sem pasta própria por projeto.
- Arquivo na raiz do repositório entra em `<Folder Name="/SolutionItems/">`, exceto o próprio `.slnx`.
- Arquivo ignorado pelo git (`bin/`, `obj/`, `.idea/`) não entra.
- Pastas e arquivos em ordem alfabética, sem distinção de maiúsculas.

Ao criar, mover ou remover um arquivo — inclusive `.md` em `docs/` ou `.claude/` — a mudança no `.slnx` vai no mesmo commit, porque tem o mesmo motivo. Antes de commitar, compare `git ls-files` com as entradas do `.slnx`: todo arquivo rastreado fora de um diretório de projeto tem seu `<File Path>` na pasta que espelha o diretório, todo `.csproj` tem seu `<Project Path>`, e nenhuma entrada aponta para arquivo não rastreado.

## Build e testes

```
dotnet build FundDistributionPlatform.slnx
dotnet test FundDistributionPlatform.slnx
```

A CI em `.github/workflows/ci.yml` executa os mesmos comandos em push e pull request na `main`, com o SDK fixado em `global.json`, e publica as APIs com Native AOT (`dotnet publish -c Release -r linux-x64`), a única verificação que o build não cobre; um comando novo na CI entra também aqui e no README. Valide os dois antes de encerrar mudanças em código de produção ou testes .NET. Para documentação e instruções, use a revisão dos exemplos e a conferência do `.slnx`; não há validador de estrutura nem de formato de documentos, por decisão registrada no guia. Uma execução aprovada serve para a mesma versão quando arquivos, configuração, comando e dependências relevantes não mudaram. Amplie ou repita checks somente quando a mudança, uma falha ou uma incerteza justificar.

A tabela de Acceptance Criteria do PRD 0003 é a fonte dos casos de teste do processamento do livro (BookBuilding): cada linha vira um teste nomeado pelo caso da tabela, traduzido para inglês no formato da convenção de nomes (Convenções de código), com o livro, `D`, `Dn`, `D'`, `E`, o ramo e a alocação por reserva exatamente como a tabela diz. Mudança na tabela ou em ALLOC-05 a ALLOC-21 atualiza os testes no mesmo commit; a divergência entre PRD e teste é defeito.

## Convenções de código

- Propriedades comuns a todos os projetos (`TargetFramework`, `Nullable`, `ImplicitUsings`) ficam em `Directory.Build.props`; os csproj não as repetem.
- Versões de pacote são centralizadas em `Directory.Packages.props` (Central Package Management). `PackageReference` nos csproj **não leva `Version`**; pacote novo entra como `PackageVersion` no props e como `PackageReference` sem versão no csproj.
- Nome de teste em snake_case, em inglês, descrevendo o comportamento verificado no formato `Sujeito_condição_resultado`, como `Failing_operation_records_error_and_exception_then_rethrows`. Sem prefixo `Test`, sem `Should` e sem `Given/When/Then`: o nome é a especificação legível na saída do runner, e o formato fixo evita que cada arquivo invente o seu.

Para código de produção, siga as regras de `.claude/rules` (Uso com Claude Code): Native AOT, versionamento, composição, módulos e tracing.

## Linguagem do domínio

Princípios da mentoria de arquitetura de Elemar Jr. (2026) aplicáveis ao projeto. Consulte-os ao definir conceitos, nomes e fronteiras.

- **Conceito antes do termo.** Fixe significado e relações antes de escolher o nome: semântica pesa mais que sintaxe.
- **Comunidade por idioma.** Os PRDs usam a linguagem brasileira de ofertas públicas; o código usa o termo da comunidade anglófona para o mesmo conceito. Verifique nomes novos em fonte primária e cite-a na decisão. Exemplo: `Lapsed` para oferta que não atinge o mínimo. Sem termo consagrado, espelhe o português e registre a lacuna, sem inventar falsa equivalência.
- **Colisão é defeito.** Um termo com outro significado na mesma comunidade deve ser corrigido, mesmo com glossário explicativo. “Cancelada” para mínimo não atingido conflita com o uso regulatório citado nos PRDs.
- **Sinônimos e fronteiras.** Dentro de um contexto, escolha um termo canônico e registre sinônimos. Termos iguais com regras distintas podem indicar fronteiras; não unifique contextos sem examinar significado e motivos de mudança.
- **Glossário como fonte.** Tipos, estados, eventos e campos derivam do glossário do PRD. Se faltar um conceito necessário, atualize o glossário antes do código. Preserve relações, além da lista de nomes.
- **Do texto ao modelo.** Extraia conceitos e significados, depois relações, instâncias/classes, atributos e restrições. Cada etapa deve ser verificável com as fontes e o especialista, respeitando a autonomia e a política de perguntas da sessão.
- **Operações de negócio.** Nomeie operações pelo motivo da mudança de estado, como fechar o livro ou revogar a oferta; evite `SetX`/`UpdateX`. Setters são privados por padrão. Evento de domínio reconhece mudança relevante para outro contexto; não publique evento sem consumidor.
- **Persistência por contexto.** Cada contexto persiste sua visão; integração ocorre por evento ou consulta ao dono, sem tabela ou modelo compartilhado. Offering é upstream e BookBuilding é core. Mudança incompatível de contrato só é tolerada partindo do Offering.

## Decisões e complexidade

- **Toda decisão tem um lado ruim.** Uma decisão de arquitetura ou de modelo só está pronta quando seu custo está nomeado. Os PRDs usam os rótulos fixos `*Cost:*` e `*Reason:*`, com conteúdo em português. Se não há lado ruim identificado, a decisão não foi analisada.
- **Regra tem princípio.** Toda instrução deste arquivo carrega o porquê. Antes de aplicar um padrão (camada, interface, abstração, mediator, repositório) pergunte qual necessidade concreta ele atende neste repositório. Sem necessidade, não entra: complexidade desnecessária é custo, e reduzir acoplamento além do necessário destrói coesão.
- **Consciência situacional antes de julgar.** Para mudar comportamento, fronteira ou decisão existente, consulte o PRD, o ADR e o histórico pertinentes. Em edição localizada, leia o trecho e suas dependências; amplie a leitura se surgir uma restrição. Distinga fatos de hipóteses antes de concluir que uma decisão está errada.
- **Critérios antes da solução.** Defina e critique os critérios do design antes de avaliar abordagens. Compare alternativas reais pelo mesmo escopo e critérios, escolha uma e registre os custos. Quando só houver uma alternativa viável, explique a restrição; não invente opções.
- **Determinístico onde puder.** Verificação é build, teste e analisador estático, não leitura de código por IA. Onde há lógica de domínio há teste; getter e setter não se testa. Processo repetível sobre o código vira script ou CI no repositório, não prompt repetido; a forma de documentos e instruções é conferida na revisão.
- **Código para humanos.** O código gerado com IA segue as convenções deste arquivo e deve ser mantido sem IA, se preciso. Revise este arquivo quando instruções conflitarem entre si; instrução conflitante degrada o resultado mais que instrução faltando.
