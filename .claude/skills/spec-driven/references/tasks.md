# Tasks

**Objetivo:** decompor o design em tasks atômicas, com dependências claras, teste co-locado e rastreabilidade até o requisito: um plano que um executor sem contexto segue sem adivinhar.

Pré-requisito: design commitado, ou spec commitada quando o Design foi dispensado. Grave em `<capability>/NNNN-<change-slug>/tasks.md` (specify.md, Layout). Sem design, a estrutura (arquivos, componentes, o que reusa) vai num parágrafo no topo do `tasks.md`.

## Como o repositório testa

Antes de qualquer task, descubra como este repositório testa; não presuma ecossistema.

1. **Guias:** `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `docs/` sobre testes, thresholds em config de runner ou CI. Guia encontrado manda; cite o arquivo.
2. **Amostra:** 5–10 arquivos de teste existentes: camada, nível (unit, integration, e2e), estilo, localização, framework. A amostra é piso (nunca menos rigoroso que o existente na mesma camada), nunca teto; o teto vem da spec.
3. **Comandos:** manifests, config e CI (`*.csproj`/`*.slnx` + `dotnet test`, `package.json`, `Makefile`, `pyproject.toml`, workflows), incluindo lint, format e typecheck: o gate Build roda tudo.

Repositório sem teste algum: pergunte os tipos e os comandos. Sem guia, vale o default forte: domínio (aggregate, use case, serviço de domínio) com todas as ramificações, 1:1 com os requisitos; adapter de entrada com happy path + cada edge case + caminhos de erro; repositório com consultas principais + erro; config e schema só gate Build. Build prova que compila e integra; evidência de comportamento é assertion contra o resultado que a spec define.

O resultado vai no `tasks.md` como um parágrafo ("como este repositório testa: guias, piso, camadas") e a tabela **Comandos de Gate**, gerada do repositório:

| Gate | Quando | Comando |
|---|---|---|
| Quick | Task com unit test | … |
| Full | Task com integration/e2e | … |
| Build | Última task da fase; task sem teste | build + lint + todos os testes |

## Task atômica

Uma task = um entregável coeso, verificável e integrável: um componente, uma função, um endpoint, um handler, com o que ele precisa para ser verificado e integrado na mesma task (implementação, teste, registro indispensável como DI, rota ou migration). "Implementar autenticação" não é task; "criar `ReservationService.Place` com idempotência, testes e registro no módulo" é. Dois entregáveis independentes na mesma task se dividem.

**Teste co-locado.** Task que cria ou modifica camada com tipo de teste exigido inclui escrever os testes na mesma task. "Testado na task N" é adiamento. Se o código só é testável depois de outra task (controller antes do wiring), mova os testes para onde ficam executáveis (merge forward) ou absorva a dependência (merge backward). Nenhuma task produz código não verificado.

| Campo | Conteúdo |
|---|---|
| **O quê** | Uma frase: o entregável exato |
| **Onde** | Paths reais de todos os arquivos que a task cria ou modifica |
| **Depende de** | IDs de task ou `nenhuma`; só para trás ou na mesma fase; sem ciclo |
| **Requisito** | IDs da spec que a task atende; refactor cita os IDs que preserva |
| **Interfaces** | *Consome:* o que usa de tasks anteriores, com assinatura. *Produz:* o que tasks posteriores usam: nomes, parâmetros, retornos. O executor só vê a própria task |
| **Pronto quando** | Critérios binários: ao menos um de comportamento (o resultado que a spec define) e o comando de gate |
| **Tests** | `unit`, `integration`, `e2e` (lista) ou `none` sozinho |
| **Gate** | `quick`, `full` ou `build`; todo valor tem linha em Comandos de Gate; integration/e2e exige `full`; `none` exige `build` |

Sem placeholder: "escrever testes para o acima" sem dizer quais, "similar à T3" (repita; o executor pode ler fora de ordem), tipo ou método que nenhuma task nem o design define.

## Fases e dependências

Fases por coesão e dependência (fundação → domínio → adapters → integração), não por tamanho; executam em sequência, tasks em ordem dentro da fase. Dependência aponta só para trás ou para a mesma fase; sem ciclo. O **Plano de execução** lista as fases e a ordem; **Tasks** tem o corpo; **Rastreabilidade** mapeia requisito → tasks. **Desvios** só é criada no Execute, quando há desvio. Tasks de correção do Verify usam IDs `TCn` sob `## Tasks de correção` e ficam fora do plano. Mudança que toca só parte dos requisitos da spec declara `scope:` no comentário de máquina (specify.md, Layout).

## Template

```markdown
<!-- sdd: tasks | spec: ../spec.md | design: ./design.md -->
# Reserva Parcial — Tasks

Como este repositório testa: `CLAUDE.md` manda xUnit em `tests/UnitTests` e `tests/IntegrationTests`; a amostra usa `[Fact]` + FluentAssertions, um arquivo por classe; domínio 1:1 com requisitos.

## Comandos de Gate

| Gate | Quando | Comando |
|---|---|---|
| Quick | Task com unit test | `dotnet test tests/UnitTests` |
| Full | Task com integration/e2e | `dotnet test FundDistributionPlatform.slnx` |
| Build | Última da fase; task sem teste | `dotnet build FundDistributionPlatform.slnx && dotnet test FundDistributionPlatform.slnx` |

## Plano de execução

### Fase 1: Domínio
T1 → T2

## Tasks

### T1: Criar `PartialReservation` value object
- **O quê:** value object com a quantidade reservada, validação contra o investimento mínimo (RSV-07) e seus testes unitários
- **Onde:** `src/ReservationBook/Reservations/PartialReservation.cs`; `tests/UnitTests/Reservations/PartialReservationTests.cs`
- **Depende de:** nenhuma
- **Requisito:** RSV-07, RSV-08
- **Interfaces:**
  - Consome: `Quantity`, `InvestmentLimits`
  - Produz: `PartialReservation.Create(Quantity amount, InvestmentLimits limits): Result<PartialReservation, ReservationError>`
- **Pronto quando:**
  - [ ] `Create` rejeita quantidade abaixo do investimento mínimo com `ReservationError.MinInvestmentNotMet` (RSV-07)
  - [ ] `Create` aceita quantidade dentro dos limites e preserva o valor (RSV-08)
  - [ ] Gate passa: `dotnet test tests/UnitTests`
- **Tests:** unit
- **Gate:** quick

### T2: …

## Rastreabilidade

| Requisito | Tasks |
|---|---|
| RSV-07 | T1 |
| RSV-08 | T1, T2 |
```

Depois: `lint_tasks.py <tasks.md> --spec <spec.md>`; corrija, rode de novo, apresente e espere.
