# Tasks

**Objetivo:** decompor o design em tasks atômicas, com dependências claras, teste co-locado e rastreabilidade até o requisito. O resultado é um plano que um executor sem contexto segue sem adivinhar.

## Pré-requisito e destino

- **Pré-requisito:** o da tabela de SKILL.md, Abrir uma mudança.
- **Destino:** grave o artefato em `<capability>/NNNN-<change-slug>/tasks.md` (specify.md, Layout).
- **Sem design:** a estrutura da mudança (arquivos, componentes, o que reusa) vai num parágrafo no topo do `tasks.md`.

## Como o repositório testa

Antes de escrever qualquer task, descubra como este repositório testa; não presuma o ecossistema.

### Descoberta

1. **Guias:** leia `AGENTS.md`, `CONTRIBUTING.md` e todo arquivo em `docs/` com `test` no nome, além de thresholds em config de runner ou de CI. Guia encontrado manda: siga-o e cite o arquivo.
2. **Amostra:** leia 5–10 arquivos de teste existentes e registre camada, nível (unit, integration, e2e), estilo, localização e framework. A amostra é piso, nunca teto: nenhuma task tem menos tipos de teste (unit, integration, e2e) que a amostra na mesma camada; o teto vem da spec.
3. **Comandos:** extraia os comandos de manifests, config e CI (`*.csproj`/`*.slnx` + `dotnet test`, `package.json`, `Makefile`, `pyproject.toml`, workflows), incluindo lint, format e typecheck, porque o gate Build roda tudo isso.

### Sem teste ou sem guia

- **Repositório sem teste algum:** pergunte ao usuário quais tipos de teste e quais comandos usar.
- **Sem guia, vale o default forte:**
  - domínio (aggregate, use case, serviço de domínio): todas as ramificações, 1:1 com os requisitos;
  - adapter de entrada: happy path, cada edge case e os caminhos de erro;
  - repositório: consultas principais e erro;
  - config e schema: só o gate Build.
- **Build não é evidência de comportamento:** Build prova que compila e integra; evidência de comportamento é assertion contra o resultado que a spec define.

### Registro no `tasks.md`

O resultado da descoberta entra no `tasks.md` de duas formas:

- um parágrafo "Como este repositório testa", com guias, piso, camadas e o total de testes que o gate Build executa antes da mudança, a contagem-base que o Verify compara; a linha `Base: <hash>` entra nesse parágrafo só quando o Execute registra a base da verificação (execute.md, Antes da primeira task);
- a tabela **Comandos de Gate**, com a coluna Quando copiada desta e a coluna Comando vinda do item 3 da Descoberta:

| Gate | Quando | Comando |
|---|---|---|
| Quick | `Gate: quick` (Campos) | comando dos testes unitários |
| Full | `Gate: full` (Campos) | comando de toda a suíte |
| Build | `Gate: build` (Campos) | build + lint + todos os testes |
| Mutação | mutação obrigatória ou pedida (verify.md, Mutação) | comando da ferramenta de mutação |

A tabela dá o comando de cada gate; qual gate cada task recebe é a regra do campo `Gate` (Campos), e é lá que ela vive: a coluna Quando aponta para o campo e não repete a regra. O nome do gate na primeira coluna é um de `quick`, `full`, `build` e `Mutação`; `lint_tasks.py` acusa como HARD qualquer outro nome de linha.

A linha `Mutação` é onde o comando de mutação da mudança fica declarado quando há `tasks.md`; sem ela, a mudança não roda mutação (verify.md, Mutação). Ela não é valor do campo `Gate` de task alguma. É opcional, exceto quando a tabela Riscos e técnicas do design tem linha de um dos três riscos que obrigam mutação (verify.md, Mutação): aí `lint_tasks.py` acusa a ausência como HARD, lendo o design pelo campo `design:` do comentário de máquina ou pela opção `--design <design.md>`.

## Task atômica

Uma task é um entregável coeso, verificável e integrável: um componente, uma função, um endpoint, um handler, junto com o que ele precisa para ser verificado e integrado na mesma task (implementação, teste e o registro indispensável, como DI, rota ou migration). "Implementar autenticação" não é task; "criar `ReservationService.Place` com idempotência, testes e registro no módulo" é. Dois entregáveis independentes na mesma task se dividem em duas: se o campo `O quê` precisa de "e" para ligar dois entregáveis, são duas tasks; teste e registro do mesmo entregável não contam como segundo entregável.

### Teste co-locado

- Task que cria ou modifica uma camada com tipo de teste exigido inclui escrever esses testes na mesma task. "Testado na task N" é adiamento.
- Se o código só é testável depois de outra task (um controller antes do wiring, por exemplo), mova os testes para a task em que ficam executáveis (merge forward) ou absorva a dependência na task atual (merge backward).
- Nenhuma task produz código não verificado.

### Campos

Toda task tem os campos abaixo:

| Campo | Conteúdo |
|---|---|
| **O quê** | Uma frase: o entregável exato |
| **Onde** | Paths reais de todos os arquivos que a task cria ou modifica |
| **Depende de** | IDs de task, ou `nenhuma`. A dependência aponta só para trás na ordem do Plano de execução (fase anterior ou task anterior da mesma fase); o linter acusa o contrário |
| **Requisito** | IDs da spec que a task atende; task de refactor cita os IDs que preserva |
| **Interfaces** | *Consome:* o que a task usa de tasks anteriores, com assinatura. *Produz:* o que tasks posteriores vão usar: nomes, parâmetros, retornos. O executor só vê a própria task |
| **Pronto quando** | Critérios binários: ao menos um de comportamento (o resultado que a spec define) e o comando do gate da task, entre crases e copiado caractere a caractere da linha que o campo `Gate` aponta na tabela de Comandos de Gate; `lint_tasks.py` acusa como HARD o comando de outro gate, o item sem comando algum e o texto entre crases que não começa por um executável declarado naquela tabela |
| **Tests** | `unit`, `integration`, `e2e` (um ou mais, em lista) ou `none` sozinho |
| **Gate** | `quick`, `full` ou `build`, pelo valor de `Tests`, na ordem: a última task de cada fase exige `build`, seja qual for o `Tests`; `none` exige `build`; lista que tem `integration` ou `e2e` exige `full`; `unit` sozinho exige `quick`. Todo valor usado tem linha na tabela de Comandos de Gate, que dá o comando dele; `lint_tasks.py` acusa como HARD toda combinação de `Tests` e `Gate` fora desta regra |

### Sem placeholder

Nenhum destes entra numa task:

- "escrever testes para o acima" sem dizer quais testes;
- "similar à T3": repita o conteúdo, porque o executor pode ler as tasks fora de ordem;
- tipo ou método que nenhuma task nem o design define.

## Fases e dependências

- **Fases por coesão e dependência**, não por tamanho: fundação, depois domínio, depois adapters, depois integração. As fases executam em sequência, e as tasks executam em ordem dentro da fase.

## Seções do `tasks.md`

A lista é fechada: `lint_tasks.py` acusa como HARD a seção `##` fora dela. O nome entre parênteses é o heading do `tasks.md` escrito em inglês (SKILL.md, Idioma).

- **Comandos de Gate** (Gate Commands) dá o comando de cada gate (Registro no `tasks.md`).
- **Plano de execução** (Execution Plan) lista as fases e a ordem das tasks.
- **Tasks** tem o corpo de cada task.
- **Rastreabilidade** (Traceability) mapeia cada requisito para as tasks que o atendem; obrigatória, e o linter confere a coerência com os campos `Requisito`.
- **Desvios** (Deviations) só é criada no Execute, quando há desvio.
- **Tasks de correção** (Correction Tasks) recebe as tasks que o Verify gera: IDs `TCn` sob `## Tasks de correção`, fora do Plano de execução.

Fora da lista, no comentário de máquina: mudança que toca só parte dos requisitos da spec declara `scope:` nele (specify.md, Layout).

## Template

```markdown
<!-- sdd: tasks | spec: ../spec.md | design: ./design.md -->
# Reserva Parcial — Tasks

Como este repositório testa: `AGENTS.md` manda xUnit em `tests/UnitTests` e `tests/IntegrationTests`; a amostra usa `[Fact]` + FluentAssertions, um arquivo por classe; domínio 1:1 com requisitos. O gate Build executa 212 testes antes desta mudança.

## Comandos de Gate

| Gate | Quando | Comando |
|---|---|---|
| Quick | `Gate: quick` | `dotnet test tests/UnitTests` |
| Full | `Gate: full` | `dotnet test FundDistributionPlatform.slnx` |
| Build | `Gate: build` | `dotnet build FundDistributionPlatform.slnx && dotnet test FundDistributionPlatform.slnx` |

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

## Antes de apresentar

Rode `lint_tasks.py <tasks.md> --spec <spec.md>` e siga o ciclo de correção de SKILL.md, Scripts; depois apresente e espere.
